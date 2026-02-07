# Формы с валидацией для приложения airline
import re
from django import forms
from django.utils.dateparse import parse_date


class ProfileForm(forms.Form):
    """Форма редактирования личных данных в профиле."""
    first_name = forms.CharField(
        max_length=50,
        required=True,
        strip=True,
        label='Имя',
        error_messages={
            'required': 'Поле «Имя» обязательно для заполнения.',
            'max_length': 'Имя не должно превышать 50 символов.',
        },
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        strip=True,
        label='Фамилия',
        error_messages={
            'required': 'Поле «Фамилия» обязательно для заполнения.',
            'max_length': 'Фамилия не должна превышать 50 символов.',
        },
    )
    patronymic = forms.CharField(
        max_length=50,
        required=False,
        strip=True,
        label='Отчество',
        error_messages={
            'max_length': 'Отчество не должно превышать 50 символов.',
        },
    )
    email = forms.EmailField(
        max_length=255,
        required=True,
        label='Email',
        error_messages={
            'required': 'Поле «Email» обязательно для заполнения.',
            'invalid': 'Введите корректный email адрес.',
            'max_length': 'Email не должен превышать 255 символов.',
        },
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        strip=True,
        label='Телефон',
        error_messages={
            'max_length': 'Телефон не должен превышать 20 символов.',
        },
    )
    passport_number = forms.CharField(
        max_length=20,
        required=False,
        strip=True,
        label='Номер паспорта',
        error_messages={
            'max_length': 'Номер паспорта не должен превышать 20 символов.',
        },
    )
    birthday = forms.CharField(
        max_length=10,
        required=False,
        strip=True,
        label='Дата рождения',
    )

    def clean_first_name(self):
        value = (self.cleaned_data.get('first_name') or '').strip()
        if not value:
            raise forms.ValidationError('Поле «Имя» обязательно для заполнения.')
        if len(value) > 50:
            raise forms.ValidationError('Имя не должно превышать 50 символов.')
        return value

    def clean_last_name(self):
        value = (self.cleaned_data.get('last_name') or '').strip()
        if not value:
            raise forms.ValidationError('Поле «Фамилия» обязательно для заполнения.')
        if len(value) > 50:
            raise forms.ValidationError('Фамилия не должна превышать 50 символов.')
        return value

    def clean_patronymic(self):
        value = (self.cleaned_data.get('patronymic') or '').strip() or None
        if value and len(value) > 50:
            raise forms.ValidationError('Отчество не должно превышать 50 символов.')
        return value or ''

    def clean_phone(self):
        value = (self.cleaned_data.get('phone') or '').strip() or None
        if not value:
            return ''
        if len(value) > 20:
            raise forms.ValidationError('Телефон не должен превышать 20 символов.')
        if not re.match(r'^\+?\d+$', value):
            raise forms.ValidationError(
                'Телефон должен содержать только цифры (в начале допускается +).'
            )
        return value

    def clean_passport_number(self):
        value = (self.cleaned_data.get('passport_number') or '').strip() or None
        if not value:
            return ''
        if len(value) > 20:
            raise forms.ValidationError('Номер паспорта не должен превышать 20 символов.')
        if not re.match(r'^[\d\s]+$', value):
            raise forms.ValidationError(
                'Номер паспорта должен содержать только цифры и пробелы.'
            )
        return value

    def clean_birthday(self):
        value = (self.cleaned_data.get('birthday') or '').strip()
        if not value:
            return ''
        # Формат дд.мм.гггг
        if not re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', value):
            raise forms.ValidationError('Введите дату в формате дд.мм.гггг.')
        try:
            parts = value.split('.')
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            normalized = f'{year:04d}-{month:02d}-{day:02d}'
            parsed = parse_date(normalized)
            if not parsed:
                raise ValueError('Invalid date')
            return value
        except (ValueError, IndexError, TypeError):
            raise forms.ValidationError('Некорректная дата. Используйте формат дд.мм.гггг.')
