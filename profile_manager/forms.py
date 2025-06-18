import re

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from profile_manager.models import UserInformation, InterestingFact, Education
from django.forms import inlineformset_factory, formset_factory


def validate_russian(value: str):
    if re.search(r'[^а-яА-Я]', value):
        raise ValidationError('Присутствуют символы, отличные от кириллицы')


class LoginForm(forms.Form):
    email = forms.EmailField(label='Электронная почта')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')


class RegisterForm(forms.Form):
    email = forms.EmailField(label='Электронная почта')
    first_name = forms.CharField(max_length=20, label='Имя', validators=[validate_russian])
    last_name = forms.CharField(max_length=20, label='Фамилия', validators=[validate_russian])
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password_again = forms.CharField(widget=forms.PasswordInput, label='Повторите пароль')

    def clean(self):
        cleaned_data = super().clean()
        if User.objects.filter(email=cleaned_data.get('email')).exists():
            self.add_error('email', 'Эта почта уже зарегистрирована')
        if cleaned_data['password'] != cleaned_data['password_again']:
            self.add_error('password_again', 'Пароли не совпадают')
        return cleaned_data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserInformation
        fields = ['image', 'description', 'town', 'address', 'dt_birthday', 'status']
        widgets = {
            'dt_birthday': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class InterestingFactForm(forms.ModelForm):
    class Meta:
        model = InterestingFact
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={
                'placeholder': 'Введите интересный факт',
                'class': 'form-control'
            })
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['university', 'is_confirmed']
        widgets = {
            'university': forms.TextInput(attrs={
                'placeholder': 'Название учебного заведения',
                'class': 'form-control'
            }),
            'is_confirmed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

# Используем formset_factory вместо inlineformset_factory для более гибкого управления
InterestingFactFormSet = inlineformset_factory(
    UserInformation,
    InterestingFact,
    fields=('text',),
    extra=1,
    can_delete=True
)

EducationFormSet = inlineformset_factory(
    UserInformation,
    Education,
    fields=('university', 'is_confirmed'),
    extra=1,
    can_delete=True
)