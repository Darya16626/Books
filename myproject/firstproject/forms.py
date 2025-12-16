import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Profile
from .models import Book
from .models import Promotion, PromotionBook, Book
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate
from decimal import Decimal
from .models import Card
from django.contrib.auth.models import User
from .models import Book
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Order, OrderItem, Book
from .models import SocialPost, SocialLink
from .models import Review

class SocialPostForm(forms.ModelForm):
    class Meta:
        model = SocialPost
        fields = ['title', 'content', 'platform', 'image_url', 'client', 'is_published']  # 🔥 image_url вместо image
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок поста'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Текст поста'}),
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'image_url': forms.URLInput(attrs={  # 🔥 URL поле
                'class': 'form-control', 
                'placeholder': 'https://example.com/image.jpg'
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SocialLinkForm(forms.ModelForm):
    class Meta:
        model = SocialLink
        fields = ['vk', 'telegram', 'instagram', 'youtube', 'facebook', 'twitter']
        widgets = {
            'vk': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://vk.com/username'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://t.me/username'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/username'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/@username'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/your_profile'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/username'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Напишите ваш отзыв...'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

class ManagerReplyForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['reply_text']
        widgets = {
            'reply_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ваш ответ клиенту...'
            }),
        }

class ManagerSocialPostForm(forms.ModelForm):
    class Meta:
        model = SocialPost
        fields = ['title', 'content', 'platform', 'image_url', 'is_published']  # 🔥 image_url вместо image
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок поста'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Текст поста'}),
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'image_url': forms.URLInput(attrs={  # 🔥 URL поле
                'class': 'form-control', 
                'placeholder': 'https://example.com/image.jpg'
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdminSocialPostForm(forms.ModelForm):
    class Meta:
        model = SocialPost
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),  # 🔥 URL поле
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }











class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['book', 'quantity']

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        book = self.cleaned_data.get('book')

        if book and qty > book.stock_quantity:
            raise forms.ValidationError(f"Количество товара '{book.title}' не может превышать количество на складе ({book.stock_quantity}).")
        return qty

class OrderForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='client'),  # только клиенты
        label="Клиент"
    )

    class Meta:
        model = Order
        fields = ['user', 'delivery_address', 'payment_method']
        widgets = {
            'payment_method': forms.RadioSelect,
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
        }

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['book', 'quantity']
        widgets = {
            'book': forms.Select(attrs={'style': 'width: 100%;'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'style': 'width: 60px;'}),
        }

class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['delivery_address', 'payment_method']

class OrderItemsFormSet(forms.BaseInlineFormSet):
    # To validate or customize formset if needed
    pass

OrderItemsFormSet = forms.inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=0,
    can_delete=True
)

class AddBookToOrderForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.all(), label="Выбрать книгу")
    quantity = forms.IntegerField(min_value=1, initial=1)

class RestoreLoginForm(forms.Form):
    email = forms.EmailField(label="Email", required=True)
    backup_word = forms.CharField(label="Резервное слово", max_length=100, required=True)

class SetNewPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput,
        validators=[validate_password],
        required=True
    )
    new_password_confirm = forms.CharField(
        label="Подтвердите пароль",
        widget=forms.PasswordInput,
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("new_password")
        pw2 = cleaned_data.get("new_password_confirm")
        if pw1 and pw2 and pw1 != pw2:
            raise ValidationError("Пароли не совпадают.")
        return cleaned_data
    



class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['card_number', 'card_holder', 'expiry_date', 'cvv']
        widgets = {
            'card_number': forms.TextInput(attrs={
                'placeholder': 'XXXX XXXX XXXX XXXX',
                'maxlength': 19,
                'autocomplete': 'off'
            }),
            'expiry_date': forms.TextInput(attrs={
                'placeholder': 'MM/YY',
                'maxlength': 5,
                'autocomplete': 'off'
            }),
            'card_holder': forms.TextInput(attrs={'placeholder': 'Имя владельца'}),
            'cvv': forms.PasswordInput(attrs={
                'placeholder': 'CVV/CVC',
                'maxlength': 3,
                'autocomplete': 'off'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        card_number = cleaned_data.get('card_number', '').replace(' ', '')
        expiry_date = cleaned_data.get('expiry_date', '')
        cvv = cleaned_data.get('cvv', '')

        # Номер карты должен быть 16 цифр
        if card_number and (not card_number.isdigit() or len(card_number) != 16):
            self.add_error('card_number', "Номер карты должен содержать 16 цифр")

        # Формат expiry_date MM/YY
        if expiry_date and not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', expiry_date):
            self.add_error('expiry_date', "Формат даты должен быть MM/YY")

        # Проверка что карта не просрочена
        if expiry_date and re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', expiry_date):
            month, year = expiry_date.split('/')
            now = timezone.now()
            exp_year = 2000 + int(year)
            exp_month = int(month)
            if (exp_year < now.year) or (exp_year == now.year and exp_month < now.month):
                self.add_error('expiry_date', "Срок действия карты истек")

        # CVV 3 цифры
        if cvv and not re.match(r'^\d{3}$', cvv):
            self.add_error('cvv', "CVV должен содержать ровно 3 цифры")

        return cleaned_data


class DepositForm(forms.Form):
    amount = forms.DecimalField(label="Сумма пополнения", min_value=Decimal('10.00'), max_value=Decimal('100000.00'), max_digits=12, decimal_places=2)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not authenticate(username=self.user.username, password=password):
            raise forms.ValidationError("Неверный пароль.")
        return password


class TransferForm(forms.Form):
    to_user_email = forms.EmailField(label="Email получателя")
    to_user_card = forms.IntegerField(label="Карта получателя", required=True, widget=forms.Select())  # будет заменён динамически
    amount = forms.DecimalField(label="Сумма перевода", min_value=Decimal('10.00'), max_digits=12, decimal_places=2)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    to_user = None

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Уберём widget select для to_user_card - он будет динамическим через JS
        self.fields['to_user_card'].widget = forms.Select(choices=[('', 'Сначала введите Email получателя')])

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not authenticate(username=self.user.username, password=password):
            raise forms.ValidationError("Неверный пароль.")
        return password

    def clean_to_user_email(self):
        from django.contrib.auth.models import User
        email = self.cleaned_data.get('to_user_email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Пользователь с таким Email не существует.")
        if user == self.user:
            raise forms.ValidationError("Нельзя перевести средства самому себе.")
        self.to_user = user
        return email

    def clean_to_user_card(self):
        to_user_card = self.cleaned_data.get('to_user_card')
        # Валидируется в view, т.к. требует связи с to_user
        return to_user_card

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return amount

def format_phone_number(value: str) -> str:
    digits = ''.join(filter(str.isdigit, value))
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return value


class ClientProfileForm(forms.ModelForm):
    middle_name = forms.CharField(label="Отчество", max_length=30, required=False)
    phone = forms.CharField(label="Телефон", max_length=20, required=False,
                            widget=forms.TextInput(attrs={
                                'placeholder': '+7 (___) ___-__-__',
                                'oninput': 'formatPhoneInput(this)'
                            }))
    backup_word = forms.CharField(label="Резервное слово", max_length=100, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            profile = getattr(self.user, "profile", None)
            if profile:
                if profile.phone:
                    self.fields['phone'].initial = format_phone_number(profile.phone)
                if profile.middle_name:
                    self.fields['middle_name'].initial = profile.middle_name
                if profile.backup_word:
                    self.fields['backup_word'].initial = profile.backup_word

        letter_pattern = r'^[А-Яа-яЁёA-Za-z\- ]+$'
        self.fields['email'].widget.attrs.update({'type': 'email', 'autocomplete': 'email'})
        self.fields['first_name'].widget.attrs.update({'pattern': letter_pattern, 'title': 'Только буквы, пробелы и дефисы'})
        self.fields['last_name'].widget.attrs.update({'pattern': letter_pattern, 'title': 'Только буквы, пробелы и дефисы'})
        self.fields['middle_name'].widget.attrs.update({'pattern': letter_pattern, 'title': 'Только буквы, пробелы и дефисы'})

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not re.match(r'^[А-Яа-яЁёA-Za-z\- ]+$', first_name):
            raise ValidationError("Имя может содержать только буквы, пробелы и дефисы.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not re.match(r'^[А-Яа-яЁёA-Za-z\- ]+$', last_name):
            raise ValidationError("Фамилия может содержать только буквы, пробелы и дефисы.")
        return last_name

    def clean_middle_name(self):
        middle_name = self.cleaned_data.get('middle_name')
        if middle_name and not re.match(r'^[А-Яа-яЁёA-Za-z\- ]+$', middle_name):
            raise ValidationError("Отчество может содержать только буквы, пробелы и дефисы.")
        return middle_name

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        qs = User.objects.filter(email=email)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(filter(str.isdigit, phone))
        if digits:
            if len(digits) != 11 or not digits.startswith('7'):
                raise ValidationError("Введите корректный номер телефона в формате +7 (XXX) XXX-XX-XX")
            qs = Profile.objects.filter(phone=digits)
            if self.user:
                qs = qs.exclude(user__pk=self.user.pk)
            if qs.exists():
                raise ValidationError("Пользователь с таким номером телефона уже существует.")
        return digits

    def clean_backup_word(self):
        backup_word = self.cleaned_data.get('backup_word', '').strip()
        if backup_word and len(backup_word) > 100:
            raise ValidationError("Резервное слово не может быть длиннее 100 символов.")
        return backup_word

    def save(self, commit=True):
        new_email = self.cleaned_data.get('email').lower()
        changed_email = self.user.email.lower() != new_email if self.user else True

        user = super().save(commit=False)
        user.email = new_email
        user.username = new_email  # синхронизируем username с email
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')

        if commit:
            user.save()
            profile = user.profile
            profile.middle_name = self.cleaned_data.get('middle_name', '')
            profile.phone = self.cleaned_data.get('phone', '')
            profile.backup_word = self.cleaned_data.get('backup_word', '')
            profile.save()

            if changed_email:
                sessions = Session.objects.filter(expire_date__gte=timezone.now())
                uid_str = str(user.pk)
                for session in sessions:
                    data = session.get_decoded()
                    if str(data.get('_auth_user_id')) == uid_str:
                        session.delete()
        else:
            profile = user.profile
            profile.middle_name = self.cleaned_data.get('middle_name', '')
            profile.phone = self.cleaned_data.get('phone', '')
            profile.backup_word = self.cleaned_data.get('backup_word', '')

        return user


class ClientPasswordChangeForm(PasswordChangeForm):
    # Можно добавить кастомизацию, пока используем как есть
    pass

class PromotionForm(forms.ModelForm):
    books = forms.ModelMultipleChoiceField(
        queryset=Book.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Книги в акции"
    )

    start_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Дата и время начала"
    )
    end_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Дата и время окончания"
    )

    class Meta:
        model = Promotion
        fields = ['title', 'description', 'image_url', 'discount_percent', 'start_datetime', 'end_datetime']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['books'].initial = self.instance.promotion_books.values_list('book_id', flat=True)
            # Форматируем даты для datetime-local (ISO 8601 без секунд)
            if self.instance.start_datetime:
                self.initial['start_datetime'] = self.instance.start_datetime.strftime('%Y-%m-%dT%H:%M')
            if self.instance.end_datetime:
                self.initial['end_datetime'] = self.instance.end_datetime.strftime('%Y-%m-%dT%H:%M')


    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_datetime')
        end = cleaned_data.get('end_datetime')
        discount = cleaned_data.get('discount_percent')
        selected_books = cleaned_data.get('books')

        if start and end and start >= end:
            self.add_error('end_datetime', "Дата окончания должна быть больше даты начала")

        if discount and (discount < 1 or discount > 100):
            self.add_error('discount_percent', "Процент скидки должен быть от 1 до 100")

        # Проверяем, что выбранные книги не в других акциях
        if selected_books:
            conflicts = []
            for book in selected_books:
                conflict = Promotion.objects.filter(
                    promotion_books__book=book,
                    end_datetime__gt=timezone.now(),
                )
                if self.instance.pk:
                    conflict = conflict.exclude(pk=self.instance.pk)
                if conflict.exists():
                    conflicts.append(book.title)
            if conflicts:
                raise forms.ValidationError(f"Книги уже участвуют в других акциях: {', '.join(conflicts)}")
        return cleaned_data

    def save(self, commit=True):
        promotion = super().save(commit)
        # Обновляем связанные книги
        promotion.promotion_books.all().delete()
        books = self.cleaned_data['books']
        for book in books:
            PromotionBook.objects.create(promotion=promotion, book=book)
        return promotion

LANGUAGE_CHOICES = [
    ('', '--- Выберите язык ---'),
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
    # Добавьте другие языки по необходимости
]


class BookForm(forms.ModelForm):
    image_urls = forms.CharField(
        label="Ссылки на изображения (через запятую)",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False
    )

    language = forms.ChoiceField(
        label="Язык книги",
        choices=LANGUAGE_CHOICES,
        required=False
    )

    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'genre',
            'description',
            'price',
            'stock_quantity',
            'isbn',
            'image_urls',
            'delivery_days',
            'year_created',
            'language',
        ]

    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']
        qs = Book.objects.filter(isbn=isbn)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Книга с таким ISBN уже существует.")
        return isbn

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Не меняем оригинальную цену здесь — логика в модели-сохранении
        if commit:
            instance.save()
        return instance

def format_phone_number(raw_number: str) -> str:
    digits = ''.join(filter(str.isdigit, raw_number))
    if len(digits) != 11 or not digits.startswith('7'):
        return raw_number  # если невалидный — вернуть как есть
    # Форматируем: +7 (XXX) XXX-XX-XX
    return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


class UserAdminForm(forms.ModelForm):
    # поля для смены пароля
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput, required=False)

    # дополнительные поля не из User
    middle_name = forms.CharField(label="Отчество", max_length=30, required=False)
    phone = forms.CharField(label="Телефон", max_length=20, required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, label="Роль", required=True)
    backup_word = forms.CharField(label="Резервное слово", max_length=100, required=False)

    class Meta:
        model = User
        # ВАЖНО: здесь только поля МОДЕЛИ User!
        fields = [
            'email',
            'first_name',
            'last_name',
            # middle_name, phone, role, backup_word – это из Profile, поэтому не включаем их в Meta.fields
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # username будем прятать или не использовать, чтобы логин был по email
        if 'username' in self.fields:
            self.fields['username'].required = False
            self.fields['username'].widget = forms.HiddenInput()

        if self.instance and self.instance.pk:
            # Редактирование существующего пользователя
            profile = self.instance.profile
            self.fields['middle_name'].initial = profile.middle_name
            self.fields['phone'].initial = format_phone_number(profile.phone)
            self.fields['role'].initial = profile.role
            self.fields['backup_word'].initial = profile.backup_word

            self.fields['password1'].required = False
            self.fields['password2'].required = False
        else:
            # Создание нового пользователя
            self.fields['password1'].required = True
            self.fields['password2'].required = True

    # ======== ВАЛИДАЦИЯ ========

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 11 or not digits.startswith('7'):
            raise ValidationError("Введите корректный номер телефона в формате +7 (XXX) XXX-XX-XX")

        qs = Profile.objects.filter(phone=digits)
        if self.instance.pk:
            qs = qs.exclude(user__pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Пользователь с таким номером телефона уже существует.")
        return digits

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not re.fullmatch(r'[А-Яа-яЁёA-Za-z\- ]+', first_name):
            raise ValidationError("Имя может содержать только буквы, пробелы и дефисы.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not re.fullmatch(r'[А-Яа-яЁёA-Za-z\- ]+', last_name):
            raise ValidationError("Фамилия может содержать только буквы, пробелы и дефисы.")
        return last_name

    def clean_middle_name(self):
        middle_name = self.cleaned_data.get('middle_name')
        if middle_name and not re.fullmatch(r'[А-Яа-яЁёA-Za-z\- ]+', middle_name):
            raise ValidationError("Отчество может содержать только буквы, пробелы и дефисы.")
        return middle_name

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')

        # Если оба пароля пустые — просто ничего не меняем
        if not p1 and not p2:
            return p2

        if p1 != p2:
            raise ValidationError("Пароли не совпадают.")
        if len(p1) < 8:
            raise ValidationError("Пароль должен содержать не менее 8 символов.")
        if not re.search(r'[A-Za-z]', p1):
            raise ValidationError("Пароль должен содержать хотя бы одну букву.")
        if not re.search(r'\d', p1):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру.")
        if not re.search(r'[^\w\s]', p1):
            raise ValidationError("Пароль должен содержать хотя бы один специальный символ.")
        return p2

    # ======== СОХРАНЕНИЕ ========

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email'].lower()
        user.email = email
        user.username = email  # логинимся по email

        # Меняем пароль, только если был введён новый
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
            profile = user.profile
            profile.middle_name = self.cleaned_data.get('middle_name', '')
            profile.phone = self.cleaned_data.get('phone', '')  # в чистых цифрах из clean_phone
            profile.role = self.cleaned_data['role']
            profile.backup_word = self.cleaned_data.get('backup_word', '')
            profile.save()

        return user




class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=30, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=30, required=True)
    middle_name = forms.CharField(label="Отчество", max_length=30, required=False)

    phone = forms.CharField(
        label="Телефон",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '+7 (___) ___-__-__',
            'oninput': 'formatPhone(this)',
        }),
    )

    email = forms.EmailField(label="Email", required=True)
    backup_word = forms.CharField(
        label="Резервное слово",
        max_length=100,
        required=False,
        help_text="Слово, которое поможет восстановить доступ, если забудете пароль.",
    )

    class Meta:
        model = User
        # Здесь тоже только поля модели User
        fields = (
            "email",
            "last_name",
            "first_name",
            # middle_name, phone, backup_word – будут обработаны вручную
            "password1",
            "password2",
        )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 11 or not digits.startswith('7'):
            raise forms.ValidationError("Введите корректный номер телефона в формате +7 (XXX) XXX-XX-XX")

        if Profile.objects.filter(phone=digits).exists():
            raise forms.ValidationError("Пользователь с таким номером телефона уже существует")
        return digits

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not re.fullmatch(r'[А-Яа-яЁёA-Za-z\- ]+', first_name):
            raise forms.ValidationError("Имя может содержать только буквы, пробелы и дефисы.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not re.fullmatch(r'[А-Яа-яЁёA-Za-z\- ]+', last_name):
            raise forms.ValidationError("Фамилия может содержать только буквы, пробелы и дефисы.")
        return last_name

    def clean_middle_name(self):
        middle_name = self.cleaned_data.get('middle_name')
        if middle_name and not re.fullmatch(r'[А-Яа-яЁёA-Za-z\- ]+', middle_name):
            raise forms.ValidationError("Отчество может содержать только буквы, пробелы и дефисы.")
        return middle_name

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        user.username = email  # username = email
        user.email = email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            profile = user.profile
            profile.middle_name = self.cleaned_data.get('middle_name', '')
            profile.phone = self.cleaned_data['phone']     # уже в виде цифр из clean_phone
            profile.backup_word = self.cleaned_data.get('backup_word', '')
            profile.save()

        return user