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

class DepositForm(forms.Form):
    amount = forms.DecimalField(label="Сумма пополнения", min_value=Decimal('0.01'), max_digits=12, decimal_places=2)
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
    amount = forms.DecimalField(label="Сумма перевода", min_value=Decimal('0.01'), max_digits=12, decimal_places=2)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not authenticate(username=self.user.username, password=password):
            raise forms.ValidationError("Неверный пароль.")
        return password

    def clean_to_user_email(self):
        email = self.cleaned_data.get('to_user_email')
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Пользователь с таким Email не существует.")
        if user == self.user:
            raise forms.ValidationError("Нельзя перевести средства самому себе.")
        self.to_user = user
        return email

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.user.balance.amount < amount:
            raise forms.ValidationError("Недостаточно средств для перевода.")
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

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            profile = getattr(self.user, "profile", None)
            if profile and profile.phone:
                self.fields['phone'].initial = format_phone_number(profile.phone)
            if profile and profile.middle_name:
                self.fields['middle_name'].initial = profile.middle_name

        self.fields['email'].widget.attrs.update({'type': 'email', 'autocomplete': 'email'})
        letter_pattern = r'^[А-Яа-яЁёA-Za-z\- ]+$'
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
            profile.save()

            # Если email изменился — удалить все сессии пользователя, кроме текущей,
            # чтобы нельзя было войти по старому email или сессии
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

class BookForm(forms.ModelForm):
    image_urls = forms.CharField(
        label="Ссылки на изображения (через запятую)",
        widget=forms.Textarea(attrs={"rows": 3}),
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
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput, required=False)
    # Убираем current_password, т.к. больше не нужен

    middle_name = forms.CharField(label="Отчество", max_length=30, required=False)
    phone = forms.CharField(label="Телефон", max_length=20, required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, label="Роль", required=True)
    # is_blocked убрано из формы

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'middle_name', 'phone', 'role',
                  'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            profile = self.instance.profile
            self.fields['middle_name'].initial = profile.middle_name

            # Форматируем телефон для отображения в поле
            self.fields['phone'].initial = format_phone_number(profile.phone)

            self.fields['role'].initial = profile.role

            self.fields['password1'].required = False
            self.fields['password2'].required = False
        else:
            self.fields['password1'].required = True
            self.fields['password2'].required = True

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

    # Убираем clean_current_password, так как пароль не требуется

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 or p2:
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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.username = self.cleaned_data['email'].lower()
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            profile = user.profile
            profile.middle_name = self.cleaned_data.get('middle_name', '')
            profile.phone = self.cleaned_data.get('phone', '')  # в чистых цифрах из clean_phone
            profile.role = self.cleaned_data['role']
            # is_blocked мы не меняем тут
            profile.save()
        return user




class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=30, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=30, required=True)
    middle_name = forms.CharField(label="Отчество", max_length=30, required=False)
    phone = forms.CharField(
        label="Телефон", max_length=20, required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '+7 (___) ___-__-__',
            'oninput': 'formatPhone(this)'
        })
    )
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ("email", "last_name", "first_name", "middle_name", "phone", "password1", "password2")

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 11 or not digits.startswith('7'):
            raise forms.ValidationError("Введите корректный номер телефона в формате +7 (XXX) XXX-XX-XX")
        from .models import Profile
        if Profile.objects.filter(phone=digits).exists():
            raise forms.ValidationError("Пользователь с таким номером телефона уже существует")
        return digits

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # username = email
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile = user.profile
            profile.middle_name = self.cleaned_data['middle_name']
            profile.phone = self.cleaned_data['phone']
            profile.save()
        return user


class PasswordResetPhoneForm(forms.Form):
    phone = forms.CharField(
        label="Телефон",
        max_length=18,
        widget=forms.TextInput(attrs={
            'placeholder': '+7 (___) ___-__-__',
            'autocomplete': 'tel',
            'oninput': 'formatPhone(this)',
            'pattern': r'^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$',
        }),
        required=True,
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 11 or not digits.startswith('7'):
            raise forms.ValidationError("Введите корректный номер телефона в формате +7 (XXX) XXX-XX-XX")
        from django.contrib.auth.models import User
        if not User.objects.filter(profile__phone=digits).exists():
            raise forms.ValidationError("Пользователь с таким номером телефона не найден")
        return digits


class PasswordResetCodeForm(forms.Form):
    code = forms.CharField(label="Введите 4-значный код", max_length=4, min_length=4)
