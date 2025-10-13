from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from random import randint
from datetime import timedelta
from .forms import RegistrationForm, PasswordResetPhoneForm, PasswordResetCodeForm, UserAdminForm, BookForm
from .models import PasswordResetCode, Book
from django.db.models import Q, F
from django.db.models import Avg, Count, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Promotion, PromotionBook
from .forms import PromotionForm
from .models import Book, BookReview, ReviewReaction
from .models import Book, CartItem, Favorite
from .forms import ClientProfileForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ClientProfileForm, ClientPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import ClientProfileForm, ClientPasswordChangeForm
from django.utils import timezone
from django.contrib.sessions.models import Session
from .models import Balance, BalanceOperation
from .forms import DepositForm, TransferForm
from decimal import Decimal
from django.db import models, transaction
from django.db.models.functions import TruncDay
from django.db.models import Sum
from django.views.decorators.http import require_POST
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from io import BytesIO
from .models import Balance, CartItem

@login_required
def balance_view(request):
    user = request.user
    balance, created = Balance.objects.get_or_create(user=user)

    if request.method == 'POST':
        if 'deposit_submit' in request.POST:
            deposit_form = DepositForm(user, request.POST, prefix='deposit')
            transfer_form = TransferForm(user, prefix='transfer')
            if deposit_form.is_valid():
                amount = deposit_form.cleaned_data['amount']
                with transaction.atomic():
                    balance.amount += amount
                    balance.save()
                    BalanceOperation.objects.create(
                        from_user=None, to_user=user,
                        operation_type='deposit',
                        amount=amount
                    )
                return redirect('balance')
        elif 'transfer_submit' in request.POST:
            deposit_form = DepositForm(user, prefix='deposit')
            transfer_form = TransferForm(user, request.POST, prefix='transfer')
            if transfer_form.is_valid():
                amount = transfer_form.cleaned_data['amount']
                to_user = transfer_form.to_user
                with transaction.atomic():
                    # Снятие с баланса отправителя
                    balance.amount -= amount
                    balance.save()
                    # Пополнение баланса получателя
                    to_balance, created = Balance.objects.get_or_create(user=to_user)
                    to_balance.amount += amount
                    to_balance.save()
                    # Одна запись операции перевод
                    BalanceOperation.objects.create(
                        from_user=user, to_user=to_user,
                        operation_type='transfer',
                        amount=amount
                    )
                return redirect('balance')
    else:
        deposit_form = DepositForm(user, prefix='deposit')
        transfer_form = TransferForm(user, prefix='transfer')

    # Запрос операций пользователя, включая переводы как одну операцию
    operations = BalanceOperation.objects.filter(
        models.Q(from_user=user) | models.Q(to_user=user)
    ).order_by('-timestamp')

    # Подготовка данных для графика, сгруппированных по дате:
    ops_for_chart = BalanceOperation.objects.filter(
        models.Q(from_user=user) | models.Q(to_user=user)
    ).annotate(date=TruncDay('timestamp')).values('date').annotate(
        total_deposit=Sum('amount', filter=models.Q(operation_type='deposit')),
        total_transfer=Sum('amount', filter=models.Q(operation_type='transfer')),
    ).order_by('date')

    chart_data = {
        'dates': [op['date'].strftime("%Y-%m-%d") for op in ops_for_chart],
        'deposit': [float(op['total_deposit'] or 0) for op in ops_for_chart],
        'transfer': [float(op['total_transfer'] or 0) for op in ops_for_chart],
    }

    # Накопительный баланс рассчитываем как сумму всех операций пользователя по дате
    cumulative = 0
    cumulative_balance = []
    for i in range(len(chart_data['dates'])):
        cumulative += chart_data['deposit'][i] + chart_data['transfer'][i]
        cumulative_balance.append(cumulative)
    chart_data['cumulative_balance'] = cumulative_balance

    return render(request, 'balance.html', {
        'balance': balance,
        'deposit_form': deposit_form,
        'transfer_form': transfer_form,
        'operations': operations,
        'chart_data': chart_data,
    })

@login_required
@require_POST
def clear_balance_history(request):
    user = request.user
    BalanceOperation.objects.filter(models.Q(from_user=user) | models.Q(to_user=user)).delete()
    messages.success(request, "История операций успешно очищена.")
    return redirect('balance')

@login_required
def client_profile_view(request):
    if request.method == 'POST':
        profile_form = ClientProfileForm(request.POST, instance=request.user, user=request.user)
        password_form = ClientPasswordChangeForm(request.user, request.POST)

        if 'profile_submit' in request.POST:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Данные профиля успешно обновлены.")
                return redirect('client_profile')
            else:
                messages.error(request, "Пожалуйста, исправьте ошибки в данных профиля.")

        elif 'password_submit' in request.POST:
            if password_form.is_valid():
                user = password_form.save()

                # Удаляем все сессии пользователя кроме текущей,
                # чтобы нельзя было зайти со старым паролем
                current_session_key = request.session.session_key
                sessions = Session.objects.filter(expire_date__gte=timezone.now())
                uid_str = str(user.pk)
                for session in sessions:
                    data = session.get_decoded()
                    if str(data.get('_auth_user_id')) == uid_str and session.session_key != current_session_key:
                        session.delete()

                # Обновляем сессию текущего пользователя, чтобы не разлогиниться
                update_session_auth_hash(request, user)

                messages.success(request, "Пароль успешно изменён.")
                return redirect('client_profile')
            else:
                messages.error(request, "Пожалуйста, исправьте ошибки в форме смены пароля.")

    else:
        profile_form = ClientProfileForm(instance=request.user, user=request.user)
        password_form = ClientPasswordChangeForm(request.user)

    return render(request, 'client_profile.html', {
        'form': profile_form,
        'password_form': password_form,
    })

@login_required
def clients_book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_review':
            rating = int(request.POST.get('rating', 0))
            comment = request.POST.get('comment', '').strip()

            if rating < 1 or rating > 5:
                messages.error(request, "Оценка должна быть от 1 до 5 звёзд.")
            else:
                BookReview.objects.create(book=book, user=user, rating=rating, comment=comment)
                update_book_rating(book)
                messages.success(request, "Ваш отзыв добавлен.")

            return redirect('clients_book_detail', book_id=book.id)

        elif action == 'react':
            review_id = request.POST.get('review_id')
            is_like = request.POST.get('is_like') == 'true'

            review = get_object_or_404(BookReview, pk=review_id)
            if review.user == user:
                messages.error(request, "Нельзя лайкать или дизлайкать свои комментарии.")
            else:
                reaction, created = ReviewReaction.objects.get_or_create(
                    review=review,
                    user=user,
                    defaults={'is_like': is_like}
                )
                if not created:
                    if reaction.is_like == is_like:
                        reaction.delete()
                    else:
                        reaction.is_like = is_like
                        reaction.save()
            return redirect('clients_book_detail', book_id=book.id)

        elif action == 'delete_review':
            review_id = request.POST.get('review_id')
            review = get_object_or_404(BookReview, pk=review_id, user=user)
            review.delete()
            update_book_rating(book)
            messages.success(request, "Ваш отзыв удалён.")
            return redirect('clients_book_detail', book_id=book.id)

    reviews = (
        BookReview.objects.filter(book=book)
        .annotate(
            likes=Count('reactions', filter=Q(reactions__is_like=True)),
            dislikes=Count('reactions', filter=Q(reactions__is_like=False))
        )
        .order_by('-created_at')
    )

    context = {
        'book': book,
        'reviews': reviews,
        'user': user,
        'rating_range': range(1, 6),  # Передаём список от 1 до 5
    }
    return render(request, 'clients_book_detail.html', context)

def update_book_rating(book):
    avg_rating = BookReview.objects.filter(book=book).aggregate(avg=Avg('rating'))['avg'] or 0
    book.rating = round(avg_rating, 2)
    book.save(update_fields=['rating'])

@login_required
def client_book_catalog(request):
    books = Book.objects.all()

    q = request.GET.get('q', '').strip()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(sku__icontains=q))
    genre = request.GET.get('genre', '')
    author = request.GET.get('author', '')
    max_price = request.GET.get('max_price', '')
    min_rating = request.GET.get('min_rating', '')

    if genre:
        books = books.filter(genre=genre)
    if author:
        books = books.filter(author=author)
    if max_price:
        try:
            max_price_val = float(max_price)
            books = books.filter(price__lte=max_price_val)
        except ValueError:
            pass

    if min_rating:
        try:
            min_rating_val = float(min_rating)
            books = books.filter(rating__gte=min_rating_val)
        except ValueError:
            pass

    genres = Book.objects.values_list('genre', flat=True).distinct().order_by('genre')
    authors = Book.objects.values_list('author', flat=True).distinct().order_by('author')

    now = timezone.now()
    promotions = Promotion.objects.filter(start_datetime__lte=now, end_datetime__gte=now).order_by('-start_datetime')

    context = {
        'books': books,
        'genres': genres,
        'authors': authors,
        'promotions': promotions,
    }
    return render(request, 'client_book_catalog.html', context)


@login_required
def client_promotion_books(request, promotion_id):
    promotion = get_object_or_404(Promotion, pk=promotion_id)

    promotion_books_qs = PromotionBook.objects.select_related('book').filter(promotion=promotion)

    q = request.GET.get('q', '').strip()
    if q:
        promotion_books_qs = promotion_books_qs.filter(
            Q(book__title__icontains=q) | Q(book__sku__icontains=q)
        )

    genre = request.GET.get('genre', '')
    if genre:
        promotion_books_qs = promotion_books_qs.filter(book__genre=genre)

    author = request.GET.get('author', '')
    if author:
        promotion_books_qs = promotion_books_qs.filter(book__author=author)

    min_price = request.GET.get('min_price')
    if min_price:
        try:
            min_price_val = float(min_price)
            promotion_books_qs = promotion_books_qs.filter(book__price__gte=min_price_val)
        except ValueError:
            pass

    max_price = request.GET.get('max_price')
    if max_price:
        try:
            max_price_val = float(max_price)
            promotion_books_qs = promotion_books_qs.filter(book__price__lte=max_price_val)
        except ValueError:
            pass

    min_rating = request.GET.get('min_rating')
    if min_rating:
        try:
            min_rating_val = float(min_rating)
            promotion_books_qs = promotion_books_qs.filter(book__rating__gte=min_rating_val)
        except ValueError:
            pass

    promotion_books_qs = promotion_books_qs.order_by('book__price')

    genres = Book.objects.filter(promotion_on_book__promotion=promotion).values_list('genre', flat=True).distinct().order_by('genre')
    authors = Book.objects.filter(promotion_on_book__promotion=promotion).values_list('author', flat=True).distinct().order_by('author')

    rating_choices = ['0', '1', '2', '3', '4', '5']

    context = {
        'promotion': promotion,
        'books': promotion_books_qs,
        'genres': genres,
        'authors': authors,
        'rating_choices': rating_choices,
    }
    return render(request, 'promotion_books.html', context)


# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Book, CartItem, Favorite

@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    cart_item, created = CartItem.objects.get_or_create(user=request.user, book=book)
    if not created:
        if cart_item.quantity < book.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Количество товара '{book.title}' увеличено в корзине.")
        else:
            messages.warning(request, "Достигнуто максимальное количество на складе.")
    else:
        messages.success(request, f"Товар '{book.title}' добавлен в корзину.")
    return redirect('client_book_catalog')

@login_required
def add_to_favorites(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, book=book)
    if created:
        messages.success(request, f"Товар '{book.title}' добавлен в избранное.")
    else:
        messages.info(request, f"Товар '{book.title}' уже в избранном.")
    return redirect('client_book_catalog')

@login_required
def cart_view(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('book')

    if request.method == 'POST':
        action = request.POST.get('action')
        item_id = request.POST.get('item_id')
        cart_item = get_object_or_404(CartItem, pk=item_id, user=user)

        if action == 'increase':
            if cart_item.quantity < cart_item.book.stock_quantity:
                cart_item.quantity += 1
                cart_item.save()
            else:
                messages.warning(request, "Достигнуто максимальное количество на складе.")
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
        elif action == 'remove':
            cart_item.delete()

        return redirect('cart_view')

    total_price = sum(item.get_total_price() for item in cart_items)
    balance, created = Balance.objects.get_or_create(user=user)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'balance': balance,  # передаем баланс для отображения на странице
    }
    return render(request, 'cart.html', context)

@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('book')

    if request.method == 'POST':
        action = request.POST.get('action')
        fav_id = request.POST.get('fav_id')
        favorite = get_object_or_404(Favorite, pk=fav_id, user=request.user)
        if action == 'remove':
            favorite.delete()
            messages.success(request, "Товар удалён из избранного.")
        return redirect('favorites_view')

    context = {
        'favorites': favorites,
    }
    return render(request, 'favorites.html', context)



def is_admin(user):
    if not user.is_authenticated or user.profile.is_blocked:
        return False
    if user.email == 'admin@example.com':
        if user.profile.role != 'admin':
            user.profile.role = 'admin'
            user.profile.save()
        return True
    return user.profile.role == 'admin'

@login_required
@user_passes_test(is_admin)
def promotion_books_select(request, promotion_id):
    promotion = get_object_or_404(Promotion, pk=promotion_id)
    books = Book.objects.all()

    query = request.GET.get('search', '').strip()
    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query) | Q(genre__icontains=query))

    genres = Book.objects.values_list('genre', flat=True).distinct().order_by('genre')
    authors = Book.objects.values_list('author', flat=True).distinct().order_by('author')

    genre = request.GET.get('genre', '')
    author = request.GET.get('author', '')

    if genre:
        books = books.filter(genre=genre)
    if author:
        books = books.filter(author=author)

    # Получаем книги, уже добавленные в акцию
    selected_book_ids = promotion.promotion_books.values_list('book_id', flat=True)

    if request.method == 'POST':
        selected_books = request.POST.getlist('selected_books')
        # Удаляем все текущие и добавляем новые
        promotion.promotion_books.all().delete()
        for book_id in selected_books:
            book = Book.objects.filter(pk=book_id).first()
            if book:
                PromotionBook.objects.create(promotion=promotion, book=book)
        return redirect('promotion_books_list', promotion_id=promotion.id)

    return render(request, 'promotion_books_select.html', {
        'promotion': promotion,
        'books': books,
        'selected_book_ids': selected_book_ids,
        'genres': genres,
        'authors': authors,
        'search_query': query,
        'selected_genre': genre,
        'selected_author': author,
    })


@login_required
@user_passes_test(is_admin)
def promotion_books_list(request, promotion_id):
    promotion = get_object_or_404(Promotion, pk=promotion_id)
    books = promotion.promotion_books.select_related('book')

    return render(request, 'promotion_books_list.html', {
        'promotion': promotion,
        'books': books,
    })

@login_required
@user_passes_test(is_admin)
def promotions_list(request):
    # Автоудаление истекших акций
    Promotion.objects.filter(end_datetime__lt=timezone.now()).delete()

    promotions = Promotion.objects.prefetch_related('promotion_books__book').order_by('-created_at')
    return render(request, 'promotions_list.html', {'promotions': promotions})

@login_required
@user_passes_test(is_admin)
def promotion_create(request):
    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Акция успешно создана")
            return redirect('promotions_list')
    else:
        form = PromotionForm()
    return render(request, 'promotion_form.html', {'form': form, 'create': True})

@login_required
@user_passes_test(is_admin)
def promotion_edit(request, promotion_id):
    promotion = get_object_or_404(Promotion, pk=promotion_id)
    if request.method == 'POST':
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            form.save()
            messages.success(request, "Акция успешно обновлена")
            return redirect('promotions_list')
    else:
        form = PromotionForm(instance=promotion)
    return render(request, 'promotion_form.html', {'form': form, 'create': False, 'promotion': promotion})

@login_required
@user_passes_test(is_admin)
def promotion_delete(request, promotion_id):
    promotion = get_object_or_404(Promotion, pk=promotion_id)
    if request.method == 'POST':
        promotion.delete()
        messages.success(request, "Акция удалена")
        return redirect('promotions_list')
    return render(request, 'promotion_confirm_delete.html', {'promotion': promotion})

@login_required
@user_passes_test(is_admin, login_url='login')
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    return render(request, 'book_detail.html', {'book': book})

@login_required
@user_passes_test(is_admin, login_url='login')
def book_catalog(request):
    books = Book.objects.all().order_by('title')

    query = request.GET.get('search', '').strip()
    if query:
        books = books.filter(Q(title__icontains=query) | Q(sku__icontains=query))

    genre = request.GET.get('genre', '')
    author = request.GET.get('author', '')
    min_rating = request.GET.get('min_rating', '')
    max_price = request.GET.get('max_price', '')

    if genre:
        books = books.filter(genre=genre)
    if author:
        books = books.filter(author=author)  # точное совпадение для select
    if min_rating:
        try:
            min_rating_val = float(min_rating)
            books = books.filter(rating__gte=min_rating_val)
        except ValueError:
            pass
    if max_price:
        try:
            max_price_val = float(max_price)
            books = books.filter(price__lte=max_price_val)
        except ValueError:
            pass

    genres = Book.objects.values_list('genre', flat=True).distinct().order_by('genre')
    authors = Book.objects.values_list('author', flat=True).distinct().order_by('author')

    return render(request, 'book_catalog.html', {
        'books': books,
        'search_query': query,
        'selected_genre': genre,
        'author_filter': author,
        'min_rating': min_rating,
        'max_price': max_price,
        'genres': genres,
        'authors': authors,
    })


@login_required
@user_passes_test(is_admin)
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Книга успешно добавлена.")
            return redirect('book_catalog')
    else:
        form = BookForm()
    return render(request, 'book_form.html', {'form': form, 'create': True})

@login_required
@user_passes_test(is_admin)
def book_edit(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Книга успешно обновлена.")
            return redirect('book_catalog')
    else:
        form = BookForm(instance=book)
    return render(request, 'book_form.html', {'form': form, 'create': False, 'book': book})

@login_required
@user_passes_test(is_admin, login_url='login')
def book_delete(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Книга удалена.")
        return redirect('book_catalog')
    return render(request, 'book_confirm_delete.html', {'book': book})


def is_admin(user):
    if not user.is_authenticated or user.profile.is_blocked:
        return False
    if user.email == 'admin@example.com':
        if user.profile.role != 'admin':
            user.profile.role = 'admin'
            user.profile.save()
        return True
    return user.profile.role == 'admin'


@user_passes_test(is_admin, login_url='login')
def admin_users_list(request):
    users = User.objects.exclude(pk=request.user.pk).order_by('email')
    return render(request, 'admin_users_list.html', {'users': users})

@user_passes_test(is_admin, login_url='login')
def admin_users_list(request):
    users = User.objects.exclude(pk=request.user.pk).order_by('email')
    return render(request, 'admin_users_list.html', {'users': users})


@user_passes_test(is_admin, login_url='login')
def admin_user_create(request):
    if request.method == 'POST':
        form = UserAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Пользователь успешно создан")
            return redirect('admin_users_list')
    else:
        form = UserAdminForm()
    return render(request, 'admin_user_form.html', {'form': form, 'create': True})


@user_passes_test(is_admin, login_url='login')
def admin_user_edit(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Пользователь обновлен")
            return redirect('admin_users_list')
    else:
        form = UserAdminForm(instance=user_obj)
    return render(request, 'admin_user_form.html', {'form': form, 'create': False, 'user_obj': user_obj})


@user_passes_test(is_admin, login_url='login')
def admin_user_delete(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        if user_obj.pk == request.user.pk:
            messages.error(request, "Нельзя удалить самого себя")
            return redirect('admin_users_list')
        user_obj.delete()
        messages.success(request, "Пользователь удалён")
        return redirect('admin_users_list')
    return render(request, 'admin_user_confirm_delete.html', {'user_obj': user_obj})


@user_passes_test(is_admin, login_url='login')
def admin_user_toggle_block(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if user_obj.pk == request.user.pk:
        messages.error(request, "Нельзя блокировать/разблокировать самого себя")
        return redirect('admin_users_list')
    profile = user_obj.profile
    profile.is_blocked = not profile.is_blocked
    profile.save()
    status = "заблокирован" if profile.is_blocked else "разблокирован"
    messages.success(request, f"Пользователь {status}")
    return redirect('admin_users_list')


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect("client_page")
    else:
        form = RegistrationForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.profile.is_blocked:
                    form.add_error(None, "Ваш аккаунт заблокирован")
                else:
                    # Форсируем роль admin для admin@example.com при каждом логине
                    if user.email == 'admin@example.com':
                        if user.profile.role != 'admin':
                            user.profile.role = 'admin'
                            user.profile.save()
                        role = 'admin'
                    else:
                        role = user.profile.role

                    login(request, user)
                    if role == 'admin':
                        return redirect("admin_page")
                    elif role == 'manager':
                        return redirect("manager_page")
                    else:
                        return redirect("client_page")
            else:
                form.add_error(None, "Неверный email или пароль")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


@login_required
def admin_page(request):
    # Форсируем роль admin для admin@example.com
    if request.user.email == 'admin@example.com':
        if request.user.profile.role != 'admin':
            request.user.profile.role = 'admin'
            request.user.profile.save()

    if not (request.user.profile.role == 'admin' and not request.user.profile.is_blocked):
        return HttpResponseForbidden("Доступ запрещён")
    return render(request, "admin_page.html")


@login_required
def manager_page(request):
    if not (request.user.profile.role == 'manager' and not request.user.profile.is_blocked):
        return HttpResponseForbidden("Доступ запрещён")
    return render(request, "manager_page.html")


@login_required
def client_page(request):
    if request.user.profile.is_blocked:
        return HttpResponseForbidden("Доступ запрещён")
    if request.user.profile.role != 'client':
        return redirect('info')  # Или перенаправить по логике
    return render(request, "client_page.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


def password_reset_request_view(request):
    if request.method == 'POST':
        form = PasswordResetPhoneForm(request.POST)
        if form.is_valid():
            phone_digits = form.cleaned_data['phone']
            user = User.objects.get(profile__phone=phone_digits)

            code = f"{randint(1000, 9999)}"
            expires_at = timezone.now() + timedelta(minutes=5)
            PasswordResetCode.objects.update_or_create(
                user=user, defaults={'code': code, 'expires_at': expires_at}
            )
            print(f"Код для восстановления: {code} для пользователя с телефоном {phone_digits}")

            request.session['password_reset_phone'] = phone_digits
            return redirect('password_reset_code')
    else:
        form = PasswordResetPhoneForm()
    return render(request, 'password_reset_request.html', {'form': form})


def password_reset_code_view(request):
    phone = request.session.get('password_reset_phone')
    if not phone:
        return redirect('password_reset_request')

    if request.method == "POST":
        form = PasswordResetCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                user = User.objects.get(profile__phone=phone)
                reset_code = PasswordResetCode.objects.get(user=user, code=code)
            except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
                form.add_error('code', "Неверный код")
            else:
                if reset_code.is_expired():
                    form.add_error('code', "Срок действия кода истёк")
                else:
                    reset_code.delete()
                    login(request, user)
                    del request.session['password_reset_phone']
                    return redirect('client_page')
    else:
        form = PasswordResetCodeForm()
    return render(request, 'password_reset_code.html', {'form': form, 'phone': phone})
