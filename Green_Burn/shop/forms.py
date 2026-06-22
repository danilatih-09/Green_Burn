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
    
# Форма смены email на странице "Настройки".
# Django сам по себе не даёт готовую форму для смены email (только для пароля),
# поэтому делаем свою — она наследуется от обычной forms.Form, а не от ModelForm,
# потому что нам нужно одно-единственное поле, а не весь объект User целиком.
class EmailChangeForm(forms.Form):
    email = forms.EmailField(required=True, label="Новый email")

    # user передаём вручную при создании формы (см. views.py),
    # чтобы знать, ЧЕЙ email меняем и с кем сравнивать на уникальность.
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    # clean_<имя_поля> — специальный метод Django: вызывается автоматически
    # при form.is_valid() для проверки именно поля email.
    def clean_email(self):
        email = self.cleaned_data['email']
        # exclude(pk=self.user.pk) — исключаем самого пользователя из проверки,
        # иначе форма ругалась бы "email уже занят", даже если человек
        # просто сохранил свой текущий email без изменений.
        if User.objects.exclude(pk=self.user.pk).filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется другим пользователем.")
        return email

    # save() вызываем вручную из view после успешной валидации (is_valid() == True)
    def save(self):
        self.user.email = self.cleaned_data['email']
        self.user.save()
        return self.user