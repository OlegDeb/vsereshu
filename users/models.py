# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date  # Добавляем этот импорт

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]
    
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    date_of_birth = models.DateField(null=True, blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return self.username
    
    @property
    def age(self):
        """Рассчитывает возраст пользователя на основе даты рождения"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def display_age(self):
        """Возвращает отформатированный возраст с правильным окончанием"""
        age = self.age
        if age is None:
            return "Не указан"
        
        if age % 10 == 1 and age % 100 != 11:
            return f"{age} год"
        elif 2 <= age % 10 <= 4 and (age % 100 < 10 or age % 100 >= 20):
            return f"{age} года"
        else:
            return f"{age} лет"