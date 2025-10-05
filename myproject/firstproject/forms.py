from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=30, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=30, required=True)
    middle_name = forms.CharField(label="Отчество", max_length=30, required=False)
    phone = forms.CharField(label="Телефон", max_length=20, required=True,
                            widget=forms.TextInput(attrs={
                                'placeholder': '+7 (___) ___-__-__',
                                'oninput': 'formatPhone(this)'
                            }))
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ("email", "last_name", "first_name", "middle_name", "phone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # username = email
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            user.profile.middle_name = self.cleaned_data['middle_name']
            user.profile.phone = self.cleaned_data['phone']
            user.profile.save()
        return user
