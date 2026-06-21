from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Profile


# UserCreationForm — стандартная форма Django для регистрации (логин + пароль + подтверждение
# пароля + хэширование). Добавляем email и поля профиля, чтобы профиль сразу заполнялся
# при регистрации, а не оставался пустым до первого захода в личный кабинет
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    full_name = forms.CharField(required=False, max_length=150, label="Полное имя")
    phone = forms.CharField(required=False, max_length=30, label="Телефон")
    address = forms.CharField(required=False, max_length=255, label="Адрес доставки")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)

        if commit:
            user.email = self.cleaned_data['email']
            user.save()

            # Profile уже создан сигналом post_save из models.py — здесь только
            # дозаполняем его данными из формы регистрации
            profile = user.profile
            profile.full_name = self.cleaned_data.get('full_name', '')
            profile.phone = self.cleaned_data.get('phone', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.save()

        return user