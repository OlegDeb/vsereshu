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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['username'].help_text = 'Логин нельзя изменить'
        
        # Добавляем подсказку для даты рождения
        if self.instance.date_of_birth:
            self.fields['date_of_birth'].help_text = f'Сейчас: {self.instance.date_of_birth.strftime("%d.%m.%Y")} ({self.instance.display_age})'