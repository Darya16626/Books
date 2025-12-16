from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
from .forms import (
    RegistrationForm, UserAdminForm, BookForm,
    PromotionForm, ClientProfileForm, ClientPasswordChangeForm,
    DepositForm, TransferForm, CardForm,
    SocialPostForm, SocialLinkForm, ReviewForm,
    ManagerSocialPostForm,
)

from .models import (
     Book, Promotion, PromotionBook, BookReview, ReviewReaction,
    CartItem, Favorite, Balance, BalanceOperation, Card, Chat, Message,
)
from django.db.models import Q, Avg, Count, Sum
from django.db.models.functions import TruncDay
from django.db import models, transaction
from django.views.decorators.http import require_POST, require_GET
from decimal import Decimal
from django.http import HttpResponse
import io
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from .models import CartItem, Balance
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .models import BalanceOperation
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import RestoreLoginForm
from .forms import RestoreLoginForm, SetNewPasswordForm
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Order, OrderItem, Book
from .forms import OrderForm, OrderItemsFormSet, AddBookToOrderForm
from django.forms import modelformset_factory
from django import forms
from .forms import OrderForm, OrderItemForm, AddBookToOrderForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.forms import inlineformset_factory
from .models import Order, OrderItem, Book
from .forms import OrderForm, OrderItemForm
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Book, Order, Promotion
from .serializers import BookSerializer, OrderSerializer, PromotionSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from .models import Profile, SocialLink, SocialPost
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Avg
from .models import SocialLink, SocialPost
from .forms import SocialPostForm, SocialLinkForm
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from .models import SocialLink, SocialPost, SocialPostView, Profile
from .forms import SocialPostForm, SocialLinkForm
import json
from django.views.decorators.csrf import csrf_exempt
from .models import SocialPost, SocialLink, SocialPostView, Review
from .forms import SocialPostForm, SocialLinkForm, ReviewForm
from .forms import SocialPostForm, SocialLinkForm, ReviewForm, ManagerSocialPostForm, ManagerReplyForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Document
import os



def is_client(user):
    try:
        return hasattr(user, 'profile') and user.profile.role == 'client'
    except:
        return False


def is_manager(user):
    try:
        return hasattr(user, 'profile') and user.profile.role == 'manager'
    except:
        return False


def is_admin(user):
    try:
        return hasattr(user, 'profile') and user.profile.role == 'admin'
    except:
        return False
    
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Document

@login_required
def manager_documents(request):
    documents = Document.objects.filter(created_by=request.user).order_by('-date')[:20]
    context = {
        'documents': documents,
        'total_docs': documents.count()
    }
    return render(request, 'manager_documents.html', context)


@login_required
def document_create(request):
    if request.method == 'POST':
        doc = Document(
            title=request.POST['title'],
            type=request.POST['type'],
            client_name=request.POST['client_name'],
            client_email=request.POST['client_email'],
            client_phone=request.POST.get('client_phone', ''),
            amount=request.POST.get('amount') or None,
            content=request.POST.get('content', ''),
            created_by=request.user
        )
        if 'file' in request.FILES:
            doc.file = request.FILES['file']
        doc.save()
        messages.success(request, '✅ Документ успешно создан!')
        return redirect('manager_documents')
    
    return render(request, 'document_create.html')


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk, created_by=request.user)
    return render(request, 'document_detail.html', {'doc': doc})


@login_required
def document_edit(request, pk):
    doc = get_object_or_404(Document, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        doc.title = request.POST['title']
        doc.type = request.POST['type']
        doc.client_name = request.POST['client_name']
        doc.client_email = request.POST['client_email']
        doc.client_phone = request.POST.get('client_phone', '')
        doc.amount = request.POST.get('amount') or None
        doc.content = request.POST.get('content', '')
        
        if 'file' in request.FILES:
            # Удаляем старый файл если есть
            if doc.file and os.path.exists(doc.file.path):
                os.remove(doc.file.path)
            doc.file = request.FILES['file']
        
        doc.save()
        messages.success(request, '✅ Документ обновлен!')
        return redirect('manager_documents')
    
    return render(request, 'document_edit.html', {'doc': doc})


@login_required
def document_delete(request, pk):
    if request.method == 'POST':
        doc = get_object_or_404(Document, pk=pk, created_by=request.user)
        if doc.file and os.path.exists(doc.file.path):
            os.remove(doc.file.path)
        doc.delete()
        return JsonResponse({'status': 'success', 'message': 'Документ удален!'})
    return JsonResponse({'status': 'error'}, status=400)









@login_required
@user_passes_test(is_client)
def client_social_page(request, platform_filter=None):
    social_links, created = SocialLink.objects.get_or_create(user=request.user)
    
    # ✅ ФИКСИРОВАНИЕ ПРОСМОТРОВ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ
    all_posts_query = SocialPost.objects.filter(is_published=True).order_by('-created_at')
    if platform_filter:
        all_posts_query = all_posts_query.filter(platform=platform_filter)
    
    all_posts = all_posts_query.prefetch_related('reviews')[:20]
    
    # ✅ Увеличиваем счетчики просмотров
    for post in all_posts:
        SocialPostView.objects.get_or_create(post=post, client=request.user)
        if SocialPostView.objects.filter(post=post, client=request.user).count() == 1:
            post.unique_views += 1
        post.views += 1
        post.save(update_fields=['views', 'unique_views'])
    
    my_posts = SocialPost.objects.filter(client=request.user, is_published=True).order_by('-created_at')
    if platform_filter:
        my_posts = my_posts.filter(platform=platform_filter)
    
    # Подготавливаем данные об отзывах
    posts_with_reviews = []
    for post in all_posts:
        client_reviews = post.reviews.filter(client=request.user)
        posts_with_reviews.append({
            'post': post,
            'client_reviews': client_reviews,
            'has_reviews': client_reviews.exists()
        })
    
    context = {
        'social_links': social_links,
        'my_posts': my_posts,
        'all_posts_with_reviews': posts_with_reviews,
        'platform_filter': platform_filter,
        'platforms': SocialPost.PLATFORMS,
    }
    
    return render(request, 'client_social.html', context)


@require_POST
@login_required
@user_passes_test(is_client)
def like_post(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id, is_published=True)
    post.likes += 1
    post.save(update_fields=['likes'])
    return JsonResponse({'status': 'success', 'likes': post.likes})

@require_POST
@login_required
@user_passes_test(is_client)
def add_review(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id, is_published=True)
    
    if Review.objects.filter(post=post, client=request.user).exists():
        return JsonResponse({'status': 'error', 'message': 'Вы уже оставляли отзыв!'}, status=400)
    
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.post = post
        review.client = request.user
        review.save()
        post.comments += 1
        post.save(update_fields=['comments'])
        return JsonResponse({
            'status': 'success', 
            'review_id': review.id,
            'text': review.text[:50] + '...' if len(review.text) > 50 else review.text,
            'rating': review.rating,
        })
    return JsonResponse({'status': 'error'}, status=400)

@require_POST
@login_required
@user_passes_test(is_client)
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, client=request.user)
    post = review.post
    review.delete()
    post.comments = post.reviews.count()
    post.save(update_fields=['comments'])
    return JsonResponse({'status': 'success'})

# ✅ ✅ ✅ МЕНЕДЖЕРСКАЯ СТРАНИЦА ✅ ✅ ✅
@login_required
@user_passes_test(is_manager)
def manager_social_page(request, platform_filter=None):
    social_links, created = SocialLink.objects.get_or_create(user=request.user)
    
    posts_query = SocialPost.objects.filter(manager=request.user)
    if platform_filter:
        posts_query = posts_query.filter(platform=platform_filter)
    
    recent_posts = posts_query.prefetch_related('reviews').order_by('-created_at')[:12]
    
    all_reviews = Review.objects.filter(post__manager=request.user).select_related('post', 'client', 'manager_reply').order_by('-created_at')
    
    stats = {
        'total_posts': posts_query.count(),
        'total_views': posts_query.aggregate(Sum('views'))['views__sum'] or 0,
        'total_likes': posts_query.aggregate(Sum('likes'))['likes__sum'] or 0,
        'total_comments': all_reviews.count(),
        'avg_rating': all_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
    }
    
    context = {
        'social_links': social_links,
        'recent_posts': recent_posts,
        'all_reviews': all_reviews,
        'stats': stats,
        'platform_filter': platform_filter,
        'platforms': SocialPost.PLATFORMS,
    }
    return render(request, 'manager_social.html', context)


@require_POST
@login_required
@user_passes_test(is_manager)
def reply_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, post__manager=request.user)
    
    if review.manager_reply:
        return JsonResponse({'status': 'error', 'message': 'Уже отвечено!'}, status=400)
    
    form = ManagerReplyForm(request.POST, instance=review)
    if form.is_valid():
        review.manager_reply = request.user
        review.reply_text = form.cleaned_data['reply_text']
        review.replied_at = timezone.now()
        review.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@require_POST
@login_required
@user_passes_test(is_manager)
def delete_review_manager(request, review_id):
    review = get_object_or_404(Review, id=review_id, post__manager=request.user)
    post = review.post
    review.delete()
    post.comments = post.reviews.count()
    post.save(update_fields=['comments'])
    return JsonResponse({'status': 'success'})


@login_required
@user_passes_test(is_admin)
def admin_social_page(request, platform_filter=None):
    social_links, created = SocialLink.objects.get_or_create(user=request.user)
    
    # Фильтр по платформе
    posts_query = SocialPost.objects.filter(is_published=True)
    if platform_filter:
        posts_query = posts_query.filter(platform=platform_filter)
    
    all_posts = posts_query.order_by('-created_at')
    
    # ✅ ИСПРАВЛЕНО: статистика по клиентам
    client_stats = SocialPost.objects.filter(is_published=True).values('client__username').annotate(
        posts_count=Count('id'),
        avg_views=Avg('views'),
        avg_likes=Avg('likes'),
        total_views=Sum('views'),
        total_likes=Sum('likes')
    ).order_by('-posts_count')[:10]
    
    # ✅ ИСПРАВЛЕНО: статистика по менеджерам (ДОБАВЛЕНО)
    manager_stats = SocialPost.objects.filter(is_published=True).values('manager__username').annotate(
        posts_count=Count('id'),
        avg_views=Avg('views'),
        avg_likes=Avg('likes'),
        total_views=Sum('views'),
        total_likes=Sum('likes')
    ).order_by('-posts_count')[:10]
    
    # ✅ ИСПРАВЛЕНО: статистика отзывов БЕЗ sentiment (используем rating)
    reviews_stats = Review.objects.aggregate(
        total_reviews=Count('id'),
        avg_rating=Avg('rating'),
        five_star_reviews=Count('id', filter=Q(rating=5)),
        four_plus_reviews=Count('id', filter=Q(rating__gte=4)),
        three_star_reviews=Count('id', filter=Q(rating=3))
    )
    
    stats = {
        'total_posts': all_posts.count(),
        'published_posts': all_posts.count(),
        'vk_posts': all_posts.filter(platform='vk').count(),
        'today_posts': all_posts.filter(created_at__date=timezone.now().date()).count(),
        'total_views': all_posts.aggregate(Sum('views'))['views__sum'] or 0,
        'total_likes': all_posts.aggregate(Sum('likes'))['likes__sum'] or 0,
        'client_stats': list(client_stats),
        'manager_stats': list(manager_stats),  # ✅ ДОБАВЛЕНО
        'reviews_stats': reviews_stats,
        'platform_stats': all_posts.values('platform').annotate(
            count=Count('id'),
            avg_views=Avg('views'),
            avg_likes=Avg('likes')
        )
    }
    
    context = {
        'social_links': social_links,
        'all_posts': all_posts[:24],  # ✅ ОГРАНИЧИЛИМ количество постов
        'stats': stats,
        'platform_filter': platform_filter,
        'platforms': SocialPost.PLATFORMS,
    }
    return render(request, 'admin_social.html', context)


@login_required
@user_passes_test(is_manager)
def social_post_list(request):
    posts = SocialPost.objects.filter(manager=request.user).order_by('-created_at')
    return render(request, 'social_posts_list.html', {'posts': posts})


@login_required
@user_passes_test(is_manager)
def social_post_create(request):
    clients = User.objects.filter(profile__role='client')
    
    if request.method == 'POST':
        form = ManagerSocialPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.manager = request.user
            if clients.exists():
                post.client = clients.first()
            post.save()
            messages.success(request, '✅ Пост успешно создан!')
            return redirect('manager_social_page')
    else:
        form = ManagerSocialPostForm()
    
    context = {'form': form, 'action': 'Создать', 'clients': clients}
    return render(request, 'social_post_form.html', context)


@login_required
@user_passes_test(is_manager)
def social_post_edit(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id, manager=request.user)
    
    if request.method == 'POST':
        form = ManagerSocialPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Пост обновлен!')
            return redirect('manager_social_page')
    else:
        form = ManagerSocialPostForm(instance=post)
    
    context = {'form': form, 'post': post, 'action': 'Редактировать'}
    return render(request, 'social_post_form.html', context)


@require_POST
@login_required
@user_passes_test(is_manager)
def social_post_delete(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id, manager=request.user)
    post_title = post.title
    post.delete()
    messages.success(request, f'🗑️ Пост "{post_title}" удален!')
    return JsonResponse({'status': 'success', 'message': 'Пост удален!'})

@login_required
@user_passes_test(is_admin)
def social_stats(request):
    posts = SocialPost.objects.filter(is_published=True)
    
    stats = {
        'total': posts.count(),
        'vk': posts.filter(platform='vk').count(),
        'telegram': posts.filter(platform='telegram').count(),
        'instagram': posts.filter(platform='instagram').count(),
        'youtube': posts.filter(platform='youtube').count(),
        'avg_views': posts.aggregate(avg_views=Avg('views'))['avg_views'] or 0,
        'avg_likes': posts.aggregate(avg_likes=Avg('likes'))['avg_likes'] or 0,
        'total_views': posts.aggregate(total_views=Sum('views'))['total_views'] or 0,
        'platform_stats': posts.values('platform').annotate(
            count=Count('id'),
            avg_views=Avg('views'),
            total_likes=Sum('likes')
        ).order_by('-count')
    }
    
    return render(request, 'social_stats.html', {'stats': stats})


@csrf_exempt
@require_POST
@login_required
def social_links_update(request):
    try:
        data = json.loads(request.body)
        social_links, created = SocialLink.objects.get_or_create(user=request.user)
        
        for field in ['vk', 'telegram', 'instagram', 'youtube', 'facebook', 'twitter']:
            setattr(social_links, field, data.get(field, '').strip())
        
        social_links.save()
        return JsonResponse({'status': 'success'})
    except:
        return JsonResponse({'status': 'error'}, status=400)


@login_required
def social_post_view(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id, is_published=True)
    
    if is_client(request.user):
        SocialPostView.objects.get_or_create(post=post, client=request.user)
        post.views += 1
        if SocialPostView.objects.filter(post=post, client=request.user).count() == 1:
            post.unique_views += 1
        post.save(update_fields=['views', 'unique_views'])
    
    context = {
        'post': post,
        'social_links': post.client.social_links,
        'reviews': post.reviews.select_related('client', 'manager_reply').all()[:10]
    }
    
    return render(request, 'social_post_view.html', context)

@login_required
@user_passes_test(is_manager)
def manager_post_reviews(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id, manager=request.user)
    reviews = post.reviews.select_related('client', 'manager_reply').order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'post': post,
        'reviews': reviews,
        'avg_rating': avg_rating
    }
    return render(request, 'manager_post_reviews.html', context)

    
    







class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]



def is_manager(user):
    try:
        return user.profile.role == 'manager' or user.is_staff
    except Exception:
        return user.is_staff


@login_required
@user_passes_test(is_manager)
def manager_order_list(request):
    orders = Order.objects.select_related('user').prefetch_related('items__book').all().order_by('-created_at')
    return render(request, 'manager_order_list.html', {'orders': orders})


@login_required
@user_passes_test(is_manager)
def manager_order_edit(request, order_id=None):
    # Поиск клиентов
    client_search = request.GET.get('client_search', '').strip()
    clients_queryset = User.objects.filter(profile__role='client')
    if client_search:
        clients_queryset = clients_queryset.filter(
            Q(first_name__icontains=client_search) |
            Q(last_name__icontains=client_search) |
            Q(email__icontains=client_search)
        )

    if order_id:
        order = get_object_or_404(Order, id=order_id)
        is_new = False
        old_items = list(order.items.all())
    else:
        order = None
        is_new = True
        old_items = []

    class CustomOrderForm(OrderForm):
        user = forms.ModelChoiceField(
            queryset=clients_queryset,
            label="Клиент"
        )

    OrderItemFormSetLocal = inlineformset_factory(
        Order, OrderItem, form=OrderItemForm, extra=0, can_delete=True
    )

    # Обработка формы поиска товаров и фильтров
    book_search = request.GET.get('book_search', '').strip()
    filter_author = request.GET.get('author', '').strip()
    filter_genre = request.GET.get('genre', '').strip()
    filter_year = request.GET.get('year_created', '').strip()
    filter_language = request.GET.get('language', '').strip()

    all_books = Book.objects.all()

    # Поиск по названию, артикулу и ISBN
    if book_search:
        all_books = all_books.filter(
            Q(title__icontains=book_search) |
            Q(sku__icontains=book_search) |
            Q(isbn__icontains=book_search)
        )

    # Фильтрация по автору, жанру, году, языку
    if filter_author:
        all_books = all_books.filter(author__icontains=filter_author)
    if filter_genre:
        all_books = all_books.filter(genre__icontains=filter_genre)
    if filter_year and filter_year.isdigit():
        all_books = all_books.filter(year_created=int(filter_year))
    if filter_language:
        all_books = all_books.filter(language__icontains=filter_language)

    if request.method == 'POST':
        book_id = request.POST.get('book')
        quantity = request.POST.get('quantity')

        form = CustomOrderForm(request.POST, instance=order)
        formset = OrderItemFormSetLocal(request.POST, instance=order)

        # Логика добавления книги и сохранения заказа без изменений
        if book_id:
            try:
                book = Book.objects.get(id=book_id)
                qty = int(quantity) if quantity else 1
                if qty > book.stock_quantity:
                    messages.error(request, f"Невозможно добавить {qty} единиц товара '{book.title}', на складе доступно только {book.stock_quantity}.")
                    if order and order.id:
                        return redirect('manager_order_edit', order_id=order.id)
                    else:
                        return redirect('manager_order_edit_new')

                if is_new:
                    user = None
                    form_for_user = CustomOrderForm(request.POST)
                    if form_for_user.is_valid():
                        user = form_for_user.cleaned_data.get('user')
                    if not user:
                        user = request.user

                    order = Order.objects.create(
                        user=user,
                        delivery_address='',
                        payment_method='cash'
                    )
                    is_new = False

                order_item, created = OrderItem.objects.get_or_create(order=order, book=book)
                if not created:
                    if order_item.quantity + qty > book.stock_quantity:
                        messages.error(request, f"Суммарное количество товара '{book.title}' в заказе не может превышать {book.stock_quantity}.")
                        return redirect('manager_order_edit', order_id=order.id)
                    order_item.quantity += qty
                else:
                    order_item.quantity = qty
                order_item.save()
                messages.success(request, f"Книга '{book.title}' добавлена в заказ.")
            except Book.DoesNotExist:
                messages.error(request, "Выбранная книга не найдена.")
            except ValueError:
                messages.error(request, "Некорректное количество.")
            if order and order.id:
                return redirect('manager_order_edit', order_id=order.id)
            else:
                return redirect('manager_order_edit_new')

        if form.is_valid() and formset.is_valid():
            saved_order = form.save(commit=False)
            if is_new:
                saved_order.user = form.cleaned_data.get('user')

            user = saved_order.user
            payment_method = saved_order.payment_method
            total_price = sum((item.book.price * item.quantity) for item in formset.save(commit=False))

            try:
                with transaction.atomic():
                    active_card = Card.objects.filter(user=user, is_active=True).first()
                    balance = None
                    balance_amount = Decimal('0.00')
                    if active_card:
                        balance = Balance.objects.select_for_update().filter(user=user, card=active_card).first()
                        if balance:
                            balance_amount = balance.amount

                    if payment_method == 'card' and balance_amount < total_price:
                        messages.error(request, "Недостаточно средств на балансе для оплаты картой.")
                        return redirect(request.path)

                    for old_item in old_items:
                        book_obj = old_item.book
                        book_obj.stock_quantity += old_item.quantity
                        book_obj.save()

                    saved_order.save()
                    formset.instance = saved_order
                    new_items = formset.save(commit=False)

                    for new_item in new_items:
                        old_item = next((oi for oi in old_items if oi.book_id == new_item.book_id), None)
                        old_qty = old_item.quantity if old_item else 0
                        diff_qty = new_item.quantity - old_qty

                        if diff_qty > 0:
                            if new_item.book.stock_quantity < diff_qty:
                                messages.error(request, f"На складе недостаточно товара '{new_item.book.title}'. Сейчас доступно: {new_item.book.stock_quantity}. Измените количество.")
                                transaction.set_rollback(True)
                                return redirect(request.path)
                            new_item.book.stock_quantity -= diff_qty
                            new_item.book.save()
                        elif diff_qty < 0:
                            new_item.book.stock_quantity += abs(diff_qty)
                            new_item.book.save()

                    formset.save()

                    if payment_method == 'card' and balance:
                        balance.amount -= total_price
                        balance.save()

                    messages.success(request, "Заказ сохранён, баланс и остатки обновлены.")
                    return redirect('manager_order_edit', order_id=saved_order.id)
            except Exception as e:
                messages.error(request, f"Ошибка при сохранении заказа: {str(e)}")
        else:
            messages.error(request, "Проверьте корректность данных в форме.")
    else:
        form = CustomOrderForm(instance=order if order else None)
        formset = OrderItemFormSetLocal(instance=order)

    context = {
        'order': order,
        'form': form,
        'formset': formset,
        'all_books': all_books,
        'is_new': is_new,
        'client_search': client_search,
        'clients': clients_queryset,
        # Передача параметров поиска и фильтрации для отображения в форме
        'book_search': book_search,
        'filter_author': filter_author,
        'filter_genre': filter_genre,
        'filter_year': filter_year,
        'filter_language': filter_language,
    }
    return render(request, 'manager_order_edit.html', context)





@login_required
@user_passes_test(is_manager)
def manager_order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.delete()
        messages.success(request, "Заказ удалён.")
        return redirect('manager_order_list')
    return render(request, 'manager_order_delete_confirm.html', {'order': order})


@login_required
@user_passes_test(is_manager)
def manager_order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.delete()
        messages.success(request, "Заказ удалён.")
        return redirect('manager_order_list')
    return render(request, 'manager_order_delete_confirm.html', {'order': order})

@login_required
def order_checkout_view(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('book')
    total_price = sum(item.get_total_price() for item in cart_items)

    active_card = Card.objects.filter(user=user, is_active=True).first()
    balance = None
    balance_amount = Decimal('0.00')
    if active_card:
        balance = Balance.objects.filter(user=user, card=active_card).first()
        if balance:
            balance_amount = balance.amount

    saved_address = ''

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        delivery_address = request.POST.get('delivery_address', '').strip()

        if not delivery_address:
            messages.error(request, "Пожалуйста, укажите адрес доставки.")
        elif not payment_method:
            messages.error(request, "Пожалуйста, выберите способ оплаты.")
        elif not cart_items.exists():
            messages.error(request, "Ваша корзина пуста.")
        elif payment_method == 'card' and balance_amount < total_price:
            messages.error(request, "На балансе недостаточно денег для оплаты картой.")
        else:
            try:
                with transaction.atomic():
                    # Создаем заказ
                    order = Order.objects.create(
                        user=user,
                        delivery_address=delivery_address,
                        payment_method=payment_method
                    )
                    # Создаем элементы заказа и уменьшаем остаток на складе
                    for item in cart_items:
                        if item.book.stock_quantity < item.quantity:
                            messages.error(request, f"Недостаточно на складе книги '{item.book.title}'. Доступно {item.book.stock_quantity} шт.")
                            transaction.set_rollback(True)
                            return redirect('order_checkout')
                        OrderItem.objects.create(
                            order=order,
                            book=item.book,
                            quantity=item.quantity,
                        )
                        item.book.stock_quantity -= item.quantity
                        item.book.save()

                    # Списание денег с баланса если оплата картой
                    if payment_method == 'card' and balance and balance_amount >= total_price:
                        balance.amount -= total_price
                        balance.save()

                    # Очищаем корзину
                    cart_items.delete()
                    messages.success(request, "Заказ успешно оформлен!")
                    return redirect('client_page')
            except Exception as e:
                messages.error(request, f"Ошибка при оформлении заказа: {str(e)}")

        saved_address = delivery_address

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'saved_address': saved_address,
        'balance_amount': balance_amount,
    }
    return render(request, 'order_checkout.html', context)

@login_required
def client_order_history(request):
    user = request.user
    # Получаем все заказы пользователя с их элементами
    orders = Order.objects.filter(user=user).prefetch_related('items__book').order_by('-created_at')

    # Список скрытых заказов истории в сессии (чтобы "очистить" историю визуально)
    hidden_order_ids = request.session.get('hidden_order_ids', [])

    # Отфильтровываем для отображения только не скрытые
    visible_orders = orders.exclude(id__in=hidden_order_ids)

    return render(request, 'client_order_history.html', {'orders': visible_orders})


@login_required
def clear_order_history(request):
    if request.method == 'POST':
        user = request.user
        all_order_ids = list(Order.objects.filter(user=user).values_list('id', flat=True))
        request.session['hidden_order_ids'] = all_order_ids
        request.session.modified = True
        messages.success(request, "История заказов очищена. Заказы в системе не удалены.")
        return redirect('client_order_history')
    else:
        messages.error(request, "Недопустимый метод запроса.")
        return redirect('client_order_history')
    

@login_required
@user_passes_test(is_manager)
def manager_order_analytics(request):
    # Форма фильтрации: по пользователю и дате создания заказа
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    orders_query = Order.objects.all()
    if user_filter:
        orders_query = orders_query.filter(user__username__icontains=user_filter)
    if date_from:
        orders_query = orders_query.filter(created_at__date__gte=date_from)
    if date_to:
        orders_query = orders_query.filter(created_at__date__lte=date_to)

    # Получаем агрегированные данные для диаграммы по продуктам в отфильтрованных заказах
    data = OrderItem.objects.filter(order__in=orders_query) \
        .values('book__title') \
        .annotate(total_quantity=Sum('quantity')) \
        .order_by('-total_quantity')

    labels = [entry['book__title'] for entry in data]
    values = [entry['total_quantity'] for entry in data]

    # Для детального просмотра: список заказов с краткой информацией
    orders_summary = orders_query.select_related('user').prefetch_related('items__book').order_by('-created_at')[:50]

    context = {
        'labels': labels,
        'values': values,
        'orders': orders_summary,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'manager_order_analytics.html', context)

def analytics_view(request):
    # Получаем фильтры для каждой диаграммы отдельно из GET запроса
    title_filter = request.GET.get('title_filter', '').strip()
    genre_filter = request.GET.get('genre_filter', '').strip()
    author_filter = request.GET.get('author_filter', '').strip()
    email_filter = request.GET.get('email_filter', '').strip()

    # Фильтрация для диаграммы по наличию товаров
    books_stock = Book.objects.all()
    if title_filter:
        books_stock = books_stock.filter(title__icontains=title_filter)
    if genre_filter:
        books_stock = books_stock.filter(genre__icontains=genre_filter)
    if author_filter:
        books_stock = books_stock.filter(author__icontains=author_filter)
    books_stock_vals = books_stock.values('title', 'stock_quantity')

    book_titles_stock = [b['title'] for b in books_stock_vals]
    stock_quantities = [b['stock_quantity'] for b in books_stock_vals]

    # Фильтрация для диаграммы по рейтингу (используем те же сами фильтры, можно изменить при необходимости)
    books_rating = Book.objects.annotate(avg_rating=Avg('reviews__rating')).all()
    if title_filter:
        books_rating = books_rating.filter(title__icontains=title_filter)
    if genre_filter:
        books_rating = books_rating.filter(genre__icontains=genre_filter)
    if author_filter:
        books_rating = books_rating.filter(author__icontains=author_filter)
    books_rating_vals = books_rating.values('title', 'avg_rating')

    book_titles_rating = [b['title'] for b in books_rating_vals]
    avg_ratings = [round(b['avg_rating'] or 0, 2) for b in books_rating_vals]

    # Фильтрация для диаграммы пользователей: только клиенты с фильтром по email,
    # активные - сделали хотя бы один заказ, неактивные - не сделали ни одного
    users = User.objects.annotate(order_count=Count('orders')).filter(profile__role='client')
    if email_filter:
        users = users.filter(email__icontains=email_filter)
    total_users = users.count()
    active_users = users.filter(order_count__gt=0).count()
    inactive_users = total_users - active_users

    context = {
        # Для stock chart
        'book_titles_stock': book_titles_stock,
        'stock_quantities': stock_quantities,

        # Для rating chart
        'book_titles_rating': book_titles_rating,
        'avg_ratings': avg_ratings,

        # Для users chart
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,

        # Фильтры для сохранения в форме
        'title_filter': title_filter,
        'genre_filter': genre_filter,
        'author_filter': author_filter,
        'email_filter': email_filter,
    }
    return render(request, 'admin_analytics.html', context)


def restore_login_view(request):
    if request.method == "POST":
        form = RestoreLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            backup_word = form.cleaned_data['backup_word']
            try:
                user = User.objects.get(email__iexact=email)
                if user.profile.backup_word and user.profile.backup_word.strip().lower() == backup_word.strip().lower():
                    # Перенаправляем на страницу ввода нового пароля
                    return redirect('set_new_password', email=email)
                else:
                    form.add_error('backup_word', 'Резервное слово некорректно.')
            except User.DoesNotExist:
                form.add_error('email', 'Пользователь с таким email не найден.')
    else:
        form = RestoreLoginForm()
    return render(request, 'restore_login.html', {'form': form})

def set_new_password_view(request, email):
    user = get_object_or_404(User, email__iexact=email)
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()

            # Указываем backend для login()
            backends = settings.AUTHENTICATION_BACKENDS
            if backends:
                user.backend = backends[0]  # Используем первый backend из настроек

            login(request, user)  # Теперь сервер не выдаст ошибку

            return render(request, 'password_reset_success.html', {'user': user})
    else:
        form = SetNewPasswordForm()
    return render(request, 'set_new_password.html', {'form': form, 'email': email})


@login_required
def cart_view(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('book')

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')

        if item_id and action == 'remove':
            item_to_remove = get_object_or_404(CartItem, id=item_id, user=user)
            item_to_remove.delete()
            messages.success(request, f'Товар "{item_to_remove.book.title}" удалён из корзины.')
            return redirect('cart_view')

        if item_id and action in ['increase', 'decrease']:
            item = get_object_or_404(CartItem, id=item_id, user=user)
            if action == 'increase':
                if item.book.stock_quantity == 0:
                    messages.error(request, f"Товар '{item.book.title}' отсутствует на складе и не может быть добавлен.")
                elif item.quantity < item.book.stock_quantity:
                    item.quantity += 1
                    item.save()
                    messages.success(request, f'Количество товара "{item.book.title}" увеличено.')
                else:
                    messages.error(request, f"Нельзя добавить больше товара '{item.book.title}', чем есть на складе ({item.book.stock_quantity}).")
            elif action == 'decrease' and item.quantity > 1:
                item.quantity -= 1
                item.save()
                messages.success(request, f'Количество товара "{item.book.title}" уменьшено.')
            return redirect('cart_view')

    active_card = Card.objects.filter(user=user, is_active=True).first()
    balance_amount = Decimal('0.00')

    if active_card:
        balance = Balance.objects.filter(user=user, card=active_card).first()
        if balance:
            balance_amount = balance.amount

    total_price = sum(item.get_total_price() for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'balance_amount': balance_amount,
    }
    return render(request, 'cart.html', context)


@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    if book.stock_quantity == 0:
        messages.error(request, f"Товар '{book.title}' отсутствует на складе и не может быть добавлен в корзину.")
        return redirect('client_book_catalog')

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

def admin_design(request):
    return render(request, 'admin_design.html')

@login_required
def export_excel(request):
    user = request.user
    operations = BalanceOperation.objects.filter(
        models.Q(from_user=user) | models.Q(to_user=user)
    ).order_by('-timestamp')

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("История операций")

    # Оформление шапки и тела
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4F81BD',
        'font_color': 'white',
        'font_name': 'Arial',
        'font_size': 11,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    cell_format = workbook.add_format({
        'font_name': 'Arial',
        'font_size': 10,
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
    })

    amount_format = workbook.add_format({
        'font_name': 'Arial',
        'font_size': 10,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0.00 ₽'
    })

    headers = ["Дата и время", "Тип операции", "Карта", "От кого", "Кому", "Сумма"]
    worksheet.set_row(0, 20)  # Высота строки заголовка

    # Записываем заголовки
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)
        # Устанавливаем ширину столбцов для удобочитаемости
        if header == "Дата и время":
            worksheet.set_column(col_num, col_num, 18)
        elif header == "Сумма":
            worksheet.set_column(col_num, col_num, 10)
        else:
            worksheet.set_column(col_num, col_num, 20)

    # Заполняем данными с форматами
    for row_num, op in enumerate(operations, start=1):
        date_str = op.timestamp.strftime("%Y-%m-%d %H:%M")
        op_type = op.get_operation_type_display()
        card_str = f"**** **** **** {op.card.card_number[-4:]}" if op.card else "-"
        from_user_str = op.from_user.email if op.from_user else "-"
        to_user_str = op.to_user.email if op.to_user else "-"
        amount = None if op.operation_type in ['add_card', 'delete_card'] else op.amount

        worksheet.write(row_num, 0, date_str, cell_format)
        worksheet.write(row_num, 1, op_type, cell_format)
        worksheet.write(row_num, 2, card_str, cell_format)
        worksheet.write(row_num, 3, from_user_str, cell_format)
        worksheet.write(row_num, 4, to_user_str, cell_format)
        if amount is None:
            worksheet.write(row_num, 5, "-", cell_format)
        else:
            worksheet.write(row_num, 5, amount, amount_format)

    workbook.close()
    output.seek(0)

    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="operations_history.xlsx"'
    return response

from django.db import transaction
from django.db.models import Q
from decimal import Decimal
# ... другие импорты

@login_required
def balance_view(request):
    user = request.user
    cards = Card.objects.filter(user=user)
    
    # ✅ Функция для обновления активной карты и баланса
    def update_active_card():
        active_card = cards.filter(is_active=True).first()
        if not active_card and cards.exists():
            cards.update(is_active=False)
            active_card = cards.first()
            active_card.is_active = True
            active_card.save()
        return active_card

    active_card = update_active_card()

    balance = None
    if active_card:
        balance, _ = Balance.objects.get_or_create(user=user, card=active_card, defaults={'amount': Decimal('0.00')})

    card_form = CardForm(prefix='card')
    deposit_form = DepositForm(user, prefix='deposit')
    transfer_form = TransferForm(user, prefix='transfer')

    if request.method == 'POST':
        if 'set_active_card' in request.POST and 'active_card' in request.POST:
            try:
                new_active_card = cards.get(id=request.POST.get('active_card'))
                cards.update(is_active=False)
                new_active_card.is_active = True
                new_active_card.save()
                active_card = update_active_card()  # ✅ Обновляем
                messages.success(request, "Активная карта успешно изменена.")
            except Card.DoesNotExist:
                messages.error(request, "Выбранная карта не найдена.")
            return redirect('balance')

        if request.POST.get('delete_card_submit') == '1' and request.POST.get('delete_card_id'):
            card_id = request.POST.get('delete_card_id')
            try:
                card_to_delete = cards.get(id=card_id)
                with transaction.atomic():
                    card_to_delete.delete()
                    BalanceOperation.objects.create(from_user=user, operation_type='delete_card', card=None)
                active_card = update_active_card()  # ✅ Обновляем после удаления
                messages.success(request, "Карта успешно удалена.")
            except Card.DoesNotExist:
                messages.error(request, "Карта для удаления не найдена.")
            return redirect('balance')

        if 'add_card_submit' in request.POST:
            card_form = CardForm(request.POST, prefix='card')
            if card_form.is_valid():
                try:
                    with transaction.atomic():
                        cards.update(is_active=False)
                        card = card_form.save(commit=False)
                        card.user = user
                        card.is_active = True
                        card.is_confirmed = True
                        card.confirmation_code = None
                        card.confirmation_code_created = None
                        card.card_number = card.card_number.replace(' ', '')
                        card.save()
                        Balance.objects.get_or_create(user=user, card=card, defaults={'amount': Decimal('0.00')})
                        BalanceOperation.objects.create(from_user=user, operation_type='add_card', card=card)
                    active_card = update_active_card()  # ✅ Обновляем
                    messages.success(request, "Карта успешно добавлена и активирована.")
                    return redirect('balance')
                except Exception:
                    messages.error(request, "Ошибка при сохранении карты.")
            else:
                messages.error(request, "Ошибка в данных карты. Пожалуйста, исправьте ошибки.")

        if 'deposit_submit' in request.POST:
            deposit_form = DepositForm(user, request.POST, prefix='deposit')
            card_id = request.POST.get('card_id')
            try:
                deposit_card = cards.get(id=card_id)
            except Card.DoesNotExist:
                deposit_card = None
                messages.error(request, "Выбранная карта для пополнения не найдена.")

            if deposit_form.is_valid() and deposit_card:
                amount = deposit_form.cleaned_data['amount']
                try:
                    with transaction.atomic():
                        balance_obj, _ = Balance.objects.get_or_create(user=user, card=deposit_card)
                        balance_obj.amount += amount
                        balance_obj.save()
                        BalanceOperation.objects.create(
                            from_user=user,
                            operation_type='deposit',
                            card=deposit_card,
                            amount=amount
                        )
                    if deposit_card == active_card:  # ✅ Обновляем баланс только активной карты
                        balance.amount += amount
                        balance.save()
                    active_card = update_active_card()
                    messages.success(request, f"Баланс карты ****{deposit_card.card_number[-4:]} успешно пополнен на {amount} ₽.")
                    return redirect('balance')
                except Exception:
                    messages.error(request, "Ошибка при пополнении баланса.")
            else:
                if not deposit_card:
                    messages.error(request, "Карта для пополнения не выбрана или недействительна.")

        # ✅ ИСПРАВЛЕННАЯ ЛОГИКА ПЕРЕВОДА С ПЕРЕУСТАНОВКОЙ АКТИВНОЙ КАРТЫ
        if 'transfer_submit' in request.POST:
            transfer_form = TransferForm(user, request.POST, prefix='transfer')
            card_id = request.POST.get('card_id')  # ID карты отправителя из формы
            
            try:
                transfer_card = cards.get(id=card_id)
            except Card.DoesNotExist:
                transfer_card = None
                messages.error(request, "Выбранная карта для перевода не найдена.")

            to_user_card_id = request.POST.get('transfer-to_user_card')

            if transfer_form.is_valid() and transfer_card and to_user_card_id:
                to_user_email = transfer_form.cleaned_data['to_user_email']
                amount = transfer_form.cleaned_data['amount']
                
                try:
                    to_user = User.objects.get(email=to_user_email)
                    recipient_card = Card.objects.get(id=to_user_card_id, user=to_user)
                except (User.DoesNotExist, Card.DoesNotExist):
                    transfer_form.add_error('to_user_card', 'Карта получателя не найдена.')
                else:
                    try:
                        with transaction.atomic():
                            sender_balance = Balance.objects.get(user=user, card=transfer_card)
                            recipient_balance, _ = Balance.objects.get_or_create(
                                user=to_user, 
                                card=recipient_card,
                                defaults={'amount': Decimal('0.00')}
                            )

                            if sender_balance.amount < amount:
                                messages.error(request, "Недостаточно средств на выбранной карте.")
                            else:
                                sender_balance.amount -= amount
                                recipient_balance.amount += amount
                                sender_balance.save()
                                recipient_balance.save()
                                
                                # ✅ ГАРАНТИРОВАННОЕ СОЗДАНИЕ ЗАПИСИ ОПЕРАЦИИ
                                operation = BalanceOperation.objects.create(
                                    from_user=user,
                                    to_user=to_user,
                                    operation_type='transfer',
                                    card=transfer_card,
                                    to_card=recipient_card,
                                    amount=amount
                                )
                                operation.refresh_from_db()  # ✅ Принудительное обновление из БД
                                
                                # ✅ КЛЮЧЕВОЕ: ПЕРЕУСТАНОВЛЯЕМ АКТИВНУЮ КАРТУ ОТПРАВИТЕЛЯ
                                if transfer_card.is_active:
                                    cards.filter(is_active=True).update(is_active=False)
                                    transfer_card.is_active = True
                                    transfer_card.save()
                                
                        # ✅ ОБНОВЛЯЕМ ПЕРЕМЕННЫЕ ПОСЛЕ ТРАНЗАКЦИИ
                        active_card = update_active_card()
                        if active_card == transfer_card:
                            balance.amount = sender_balance.amount
                            balance.save()
                            
                        messages.success(request, 
                            f"✅ Успешно переведено {amount} ₽ на карту {recipient_card.card_holder} "
                            f"****{recipient_card.card_number[-4:]} ({to_user.email})"
                        )
                        return redirect('balance')
                    except Balance.DoesNotExist:
                        messages.error(request, "Баланс отправителя не найден.")
                    except Exception as e:
                        messages.error(request, f"Ошибка при переводе: {str(e)}")
            else:
                if not transfer_card:
                    messages.error(request, "Выберите карту для перевода.")
                if not to_user_card_id:
                    transfer_form.add_error('to_user_card', 'Выберите карту получателя.')

    # ✅ ПРАВИЛЬНЫЙ ФИЛЬТР ИСТОРИИ С ПРИНУДИТЕЛЬНЫМ ОБНОВЛЕНИЕМ
    operations = BalanceOperation.objects.filter(
        Q(from_user=user) | Q(to_user=user)
    ).select_related('card', 'to_card', 'from_user', 'to_user').order_by('-timestamp')[:100]
    operations = list(operations)  # ✅ Принудительно загружаем в память

    return render(request, 'balance.html', {
        'balance': balance,
        'cards': cards,
        'active_card': active_card,
        'card_form': card_form,
        'deposit_form': deposit_form,
        'transfer_form': transfer_form,
        'operations': operations,
    })




# AJAX endpoint для получения карт пользователя по email (без изменений)
@login_required
@require_GET
def ajax_get_user_cards(request):
    email = request.GET.get('email')
    if not email:
        return JsonResponse({'error': 'Email не указан', 'cards': []})
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь с таким Email не найден', 'cards': []})

    cards = Card.objects.filter(user=user, is_confirmed=True).values('id', 'card_holder', 'card_number')
    cards_list = []
    for card in cards:
        cards_list.append({
            'id': card['id'],
            'card_holder': card['card_holder'],
            'last4': card['card_number'][-4:] if card['card_number'] else '####'
        })
    return JsonResponse({'cards': cards_list})


def prepare_chart_data(user):
    ops_for_chart = BalanceOperation.objects.filter(
        Q(from_user=user) | Q(to_user=user)
    ).annotate(
        date=TruncDay('timestamp')
    ).values('date').annotate(
        total_deposit=Sum('amount', filter=Q(operation_type='deposit')),
        total_transfer=Sum('amount', filter=Q(operation_type='transfer')),
    ).order_by('date')

    chart_data = {
        'dates': [op['date'].strftime('%Y-%m-%d') for op in ops_for_chart],
        'deposit': [float(op['total_deposit'] or 0) for op in ops_for_chart],
        'transfer': [float(op['total_transfer'] or 0) for op in ops_for_chart],
    }
    cumulative = 0
    cumulative_balance = []
    for i in range(len(chart_data['dates'])):
        cumulative += chart_data['deposit'][i]
        cumulative -= chart_data['transfer'][i]
        cumulative_balance.append(cumulative)
    chart_data['cumulative_balance'] = cumulative_balance
    return chart_data

@login_required
def card_confirm(request, card_id):
    card = get_object_or_404(Card, id=card_id, user=request.user)
    if card.is_confirmed:
        messages.success(request, "Эта карта уже подтверждена.")
        return redirect('balance')

    code_lifetime_sec = 120  # 2 минуты

    if request.method == 'POST':
        input_code = request.POST.get('confirmation_code')
        now = timezone.now()

        if card.confirmation_code_created + timedelta(seconds=code_lifetime_sec) < now:
            messages.error(request, "Код подтверждения истек. Добавьте карту заново.")
            card.delete()
            return redirect('balance')

        if input_code == card.confirmation_code:
            card.is_confirmed = True
            card.is_active = True
            card.confirmation_code = None
            card.confirmation_code_created = None
            card.save()
            messages.success(request, "Карта успешно подтверждена и активирована.")
            return redirect('balance')
        else:
            messages.error(request, "Неверный код подтверждения.")

    # Вычисляем сколько секунд осталось до истечения кода, чтоб запустить таймер
    time_left = 0
    if card.confirmation_code_created:
        elapsed = (timezone.now() - card.confirmation_code_created).total_seconds()
        time_left = max(0, code_lifetime_sec - int(elapsed))

    return render(request, 'card_confirm.html', {'card': card, 'time_left': time_left})

@login_required
@require_POST
def clear_balance_history(request):
    user = request.user
    BalanceOperation.objects.filter(Q(from_user=user) | Q(to_user=user)).delete()
    messages.success(request, "История операций успешно очищена.")
    return redirect('balance')

@login_required
def edit_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, sender=request.user, is_deleted=False)
    if request.method == 'POST':
        new_text = request.POST.get('text', '').strip()
        if new_text:
            message.text = new_text
            message.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, "Текст сообщения не может быть пустым.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        return render(request, 'edit_message.html', {'message': message})


@require_POST
@login_required
def mark_as_read(request):
    # Ожидаем, что в POST придет список message_ids
    message_ids = request.POST.getlist('message_ids[]')
    updated_count = 0
    if message_ids:
        messages_to_update = Message.objects.filter(id__in=message_ids).exclude(sender=request.user).filter(is_read=False)
        updated_count = messages_to_update.update(is_read=True)
    return JsonResponse({'updated': updated_count})


@login_required
def client_support_chat(request):
    user = request.user
    if not hasattr(user, 'profile') or user.profile.role != 'client':
        return redirect('client_page')

    # Клиент выбирает менеджера: если в GET есть параметр manager_id — меняем чат
    manager_id = request.GET.get('manager_id')
    if manager_id:
        manager = User.objects.filter(id=manager_id, profile__role='manager').first()
        if not manager:
            messages.error(request, "Выбранный менеджер не найден.")
            return redirect('client_support_chat')
    else:
        # По умолчанию первый менеджер
        manager = User.objects.filter(profile__role='manager').first()
        if not manager:
            return render(request, 'client_support_chat.html', {'error': 'Менеджер не найден'})

    chat, created = Chat.objects.get_or_create(client=user, manager=manager)

    # Проверяем, удалён ли менеджер
    if chat.is_manager_deleted:
        can_send = False
        notification = "Данный работник был удален, новые сообщения отправлять нельзя."
    else:
        can_send = True
        notification = None

    if request.method == 'POST' and can_send:
        message_text = request.POST.get('message', '').strip()
        if message_text:
            Message.objects.create(chat=chat, sender=user, text=message_text)
            return redirect(f"{request.path}?manager_id={manager.id}")

    messages_list = chat.messages.filter(is_deleted=False).order_by('created_at')

    # Список менеджеров для выбора
    managers = User.objects.filter(profile__role='manager')

    context = {
        'chat': chat,
        'messages': messages_list,
        'user_role': 'client',
        'chat_partner_name': manager.get_full_name() if manager else 'Удалён',
        'managers': managers,
        'selected_manager': manager,
        'can_send': can_send,
        'notification': notification,
    }
    return render(request, 'client_support_chat.html', context)


@login_required
def delete_chat(request, chat_id):
    user = request.user
    chat = get_object_or_404(Chat, id=chat_id, client=user)
    if request.method == 'POST':
        chat.delete()
        return redirect('client_support_chat')
    return render(request, 'delete_chat_confirm.html', {'chat': chat})


@login_required
def delete_message(request, message_id):
    user = request.user
    message = get_object_or_404(Message, id=message_id, sender=user, is_deleted=False)
    chat = message.chat
    if request.method == 'POST':
        message.is_deleted = True
        message.save()
        # Перенаправляем в чат
        if user.profile.role == 'client':
            return redirect('client_support_chat')
        else:
            return redirect('manager_chat_detail', chat_id=chat.id)
    return render(request, 'delete_message_confirm.html', {'message': message})


@login_required
def manager_support_page(request):
    user = request.user
    if not hasattr(user, 'profile') or user.profile.role != 'manager':
        return redirect('manager_page')

    chats = Chat.objects.filter(manager=user).order_by('-created_at')

    context = {
        'chats': chats,
    }
    return render(request, 'manager_support_page.html', context)


@login_required
def manager_chat_detail(request, chat_id):
    user = request.user
    if not hasattr(user, 'profile') or user.profile.role != 'manager':
        return redirect('manager_page')

    chat = get_object_or_404(Chat, pk=chat_id, manager=user)

    if chat.is_manager_deleted:
        can_send = False
        notification = "Данный работник был удален, новые сообщения отправлять нельзя."
    else:
        can_send = True
        notification = None

    if request.method == 'POST' and can_send:
        message_text = request.POST.get('message', '').strip()
        if message_text:
            Message.objects.create(chat=chat, sender=user, text=message_text)
            return redirect('manager_chat_detail', chat_id=chat_id)

    messages_list = chat.messages.filter(is_deleted=False).order_by('created_at')

    unread_messages = messages_list.filter(is_read=False).exclude(sender=user)
    unread_messages.update(is_read=True)

    context = {
        'chat': chat,
        'messages': messages_list,
        'user_role': 'manager',
        'chat_partner_name': chat.client.get_full_name(),
        'can_send': can_send,
        'notification': notification,
    }
    return render(request, 'manager_chat_detail.html', context)

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
        'rating_range': range(1, 6),  # 1..5
    }
    return render(request, 'clients_book_detail.html', context)


def update_book_rating(book):
    avg_rating = BookReview.objects.filter(book=book).aggregate(avg=Avg('rating'))['avg'] or 0
    book.rating = round(avg_rating, 2)
    book.save(update_fields=['rating'])

@login_required
def client_book_catalog(request):
    books = Book.objects.all()

    # Параметры поиска и фильтров из GET-запроса
    q = request.GET.get('q', '').strip()
    genre = request.GET.get('genre', '')
    author = request.GET.get('author', '')
    max_price = request.GET.get('max_price', '')
    min_rating = request.GET.get('min_rating', '')
    language = request.GET.get('language', '')
    year_created = request.GET.get('year_created', '')
    
    if q:
        # Поиск по названию, артикулу и ISBN
        books = books.filter(
            Q(title__icontains=q)
            | Q(sku__icontains=q)
            | Q(isbn__icontains=q)
        )
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
    if language:
        books = books.filter(language=language)
    if year_created:
        try:
            year_val = int(year_created)
            books = books.filter(year_created=year_val)
        except ValueError:
            pass

    genres = Book.objects.values_list('genre', flat=True).distinct().order_by('genre')
    authors = Book.objects.values_list('author', flat=True).distinct().order_by('author')

    now = timezone.now()
    promotions = Promotion.objects.filter(start_datetime__lte=now, end_datetime__gte=now).order_by('-start_datetime')

    LANGUAGE_CHOICES = [
        ('Russian', 'Русский'),
        ('English', 'Английский'),
        ('German', 'Немецкий'),
        ('French', 'Французский'),
        ('Spanish', 'Испанский'),
        ('Chinese', 'Китайский'),
        ('Japanese', 'Японский'),
        ('Italian', 'Итальянский'),
        ('Portuguese', 'Португальский'),
        ('Arabic', 'Арабский'),
        # добавлять при необходимости
    ]

    context = {
        'books': books,
        'genres': genres,
        'authors': authors,
        'promotions': promotions,
        'language_choices': LANGUAGE_CHOICES,
        'request': request,
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
    books = Book.objects.all().order_by('title')

    query = request.GET.get('search', '').strip()
    genre = request.GET.get('genre', '').strip()
    author = request.GET.get('author', '').strip()
    min_rating = request.GET.get('min_rating', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    year = request.GET.get('year_created', '').strip()
    language = request.GET.get('language', '').strip()

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(sku__icontains=query)
            | Q(isbn__icontains=query)
        )
    if genre:
        books = books.filter(genre=genre)
    if author:
        books = books.filter(author=author)
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
    if year:
        books = books.filter(year_created=year)
    if language:
        books = books.filter(language__iexact=language)

    years = Book.objects.values_list('year_created', flat=True).distinct().order_by('year_created')
    languages = Book.objects.values_list('language', flat=True).distinct().order_by('language')
    genres = Book.objects.values_list('genre', flat=True).distinct().order_by('genre')
    authors = Book.objects.values_list('author', flat=True).distinct().order_by('author')

    selected_book_ids = set(promotion.promotion_books.values_list('book_id', flat=True))

    if request.method == 'POST':
        selected_books = request.POST.getlist('selected_books')
        # Обновление книг акции
        promotion.promotion_books.all().delete()
        for book_id in selected_books:
            book = Book.objects.filter(pk=book_id).first()
            if book:
                PromotionBook.objects.create(promotion=promotion, book=book)
        return redirect('promotion_books_select', promotion_id=promotion.id)

    context = {
        'promotion': promotion,
        'books': books,
        'selected_book_ids': selected_book_ids,
        'genres': genres,
        'authors': authors,
        'years': years,
        'languages': languages,
        'search_query': query,
        'selected_genre': genre,
        'selected_author': author,
        'min_rating': min_rating,
        'max_price': max_price,
        'selected_year': year,
        'selected_language': language,
    }

    return render(request, 'promotion_books_select.html', context)


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

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'admin_respond':
            review_id = request.POST.get('review_id')
            response_text = request.POST.get('response', '').strip()
            review = get_object_or_404(BookReview, pk=review_id)
            review.admin_response = response_text
            review.save(update_fields=['admin_response'])
            messages.success(request, "Ответ добавлен к отзыву.")
            return redirect('book_detail', book_id=book.id)

        elif action == 'delete_review':
            review_id = request.POST.get('review_id')
            review = get_object_or_404(BookReview, pk=review_id)
            review.delete()
            messages.success(request, "Отзыв удалён.")
            return redirect('book_detail', book_id=book.id)

        elif action == 'react':
            review_id = request.POST.get('review_id')
            is_like = request.POST.get('is_like') == 'true'
            review = get_object_or_404(BookReview, pk=review_id)
            user = request.user
            # Не даём лайкать/дизлайкать свои комментарии
            if review.user == user:
                messages.error(request, "Нельзя ставить реакцию на свой комментарий.")
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
            return redirect('book_detail', book_id=book.id)

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
    }
    return render(request, 'book_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')  # заменить is_admin на вашу логику проверки админа
def book_catalog(request):
    books = Book.objects.all().order_by('title')

    query = request.GET.get('search', '').strip()
    if query:
        # поиск по названию, артикулу и ISBN
        books = books.filter(
            Q(title__icontains=query) |
            Q(sku__icontains=query) |
            Q(isbn__icontains=query)
        )

    genre = request.GET.get('genre', '')
    author = request.GET.get('author', '')
    min_rating = request.GET.get('min_rating', '')
    max_price = request.GET.get('max_price', '')
    year_created = request.GET.get('year_created', '')
    language = request.GET.get('language', '')

    if genre:
        books = books.filter(genre=genre)
    if author:
        books = books.filter(author=author)
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
    if year_created:
        try:
            year_val = int(year_created)
            books = books.filter(year_created=year_val)
        except ValueError:
            pass
    if language:
        books = books.filter(language=language)

    genres = Book.objects.values_list('genre', flat=True).distinct().order_by('genre')
    authors = Book.objects.values_list('author', flat=True).distinct().order_by('author')
    languages = Book.objects.values_list('language', flat=True).distinct().order_by('language')

    return render(request, 'book_catalog.html', {
        'books': books,
        'search_query': query,
        'selected_genre': genre,
        'author_filter': author,
        'min_rating': min_rating,
        'max_price': max_price,
        'year_created': year_created,
        'selected_language': language,
        'genres': genres,
        'authors': authors,
        'languages': languages,
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


User = get_user_model()

@user_passes_test(is_admin, login_url='login')
def admin_users_list(request):
    query = request.GET.get('search', '').strip()
    users = User.objects.exclude(pk=request.user.pk).order_by('email')
    if query:
        users = users.filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    return render(request, 'admin_users_list.html', {'users': users, 'search_query': query})


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