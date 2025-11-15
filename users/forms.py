# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'date_of_birth')

class CustomUserChangeForm(UserChangeForm):
    password = None
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'date_of_birth', 'phone_number', 'gender', 'bio', 'avatar')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'username': 'Логин',
            'email': 'Электронная почта',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'date_of_birth': 'Дата рождения',
            'phone_number': 'Номер телефона',
            'gender': 'Пол',
            'bio': 'О себе',
            'avatar': 'Мое фото',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['username'].help_text = 'Логин нельзя изменить'
        
        # Добавляем подсказку для даты рождения
        if self.instance.date_of_birth:
            self.fields['date_of_birth'].help_text = f'Сейчас: {self.instance.date_of_birth.strftime("%d.%m.%Y")} ({self.instance.display_age})'
        
        # Добавляем подсказки для других полей
        self.fields['email'].help_text = 'Ваш адрес электронной почты'
        self.fields['phone_number'].help_text = 'Номер телефона в формате +7XXXXXXXXXX'
        self.fields['bio'].help_text = 'Расскажите о себе (максимум 500 символов)'
        self.fields['avatar'].help_text = 'Загрузите ваше фото'


class ComplaintForm(forms.ModelForm):
    """Форма для подачи жалобы на пользователя"""
    class Meta:
        from .models import UserComplaint
        model = UserComplaint
        fields = ('reported_user', 'complaint_type', 'description')
        widgets = {
            'reported_user': forms.Select(attrs={'class': 'form-select'}),
            'complaint_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Опишите проблему подробно...'
            }),
        }
        labels = {
            'reported_user': 'На кого пожаловаться',
            'complaint_type': 'Тип жалобы',
            'description': 'Описание проблемы',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Исключаем текущего пользователя из списка
            from .models import CustomUser
            self.fields['reported_user'].queryset = CustomUser.objects.exclude(id=user.id)
        
        self.fields['description'].help_text = 'Опишите проблему максимально подробно. Это поможет нам быстрее разобраться в ситуации.'


class WarningForm(forms.ModelForm):
    """Форма для выдачи предупреждения (только для админов)"""
    class Meta:
        from .models import UserWarning
        model = UserWarning
        fields = ('user', 'reason')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Укажите причину предупреждения...'
            }),
        }
        labels = {
            'user': 'Пользователь',
            'reason': 'Причина предупреждения',
        }


class BanForm(forms.ModelForm):
    """Форма для бана пользователя (только для админов)"""
    class Meta:
        from .models import UserBan
        model = UserBan
        fields = ('user', 'reason', 'ban_until')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Укажите причину бана...'
            }),
            'ban_until': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }
        labels = {
            'user': 'Пользователь',
            'reason': 'Причина бана',
            'ban_until': 'Бан до (оставьте пустым для постоянного бана)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ban_until'].required = False
        self.fields['ban_until'].help_text = 'Оставьте пустым для постоянного бана. Укажите дату и время для временного бана.'