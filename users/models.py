# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date  # Добавляем этот импорт
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFill
import os

def avatar_upload_path(instance, filename):
    """Генерирует путь для загрузки аватара по году и месяцу"""
    # Получаем текущую дату
    from django.utils import timezone
    now = timezone.now()
    # Формируем путь: avatars/YYYY/MM/filename
    year = now.strftime('%Y')
    month = now.strftime('%m')
    # Сохраняем оригинальное имя файла
    ext = filename.split('.')[-1]
    filename = f"{instance.username}_{now.strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('avatars', year, month, filename)

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
    avatar = ProcessedImageField(
        upload_to=avatar_upload_path,
        processors=[ResizeToFill(400, 400)],
        format='JPEG',
        options={'quality': 85},
        null=True,
        blank=True
    )
    # Миниатюра для навбара и маленьких мест
    avatar_thumbnail = ImageSpecField(
        source='avatar',
        processors=[ResizeToFill(50, 50)],
        format='JPEG',
        options={'quality': 80}
    )
    # Средний размер для профиля
    avatar_medium = ImageSpecField(
        source='avatar',
        processors=[ResizeToFill(150, 150)],
        format='JPEG',
        options={'quality': 85}
    )
    
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
    
    def get_average_rating(self):
        """Возвращает средний рейтинг пользователя на основе полученных отзывов"""
        from django.db.models import Avg
        avg_rating = self.reviews_received.aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 2) if avg_rating else None
    
    def get_reviews_count(self):
        """Возвращает количество полученных отзывов"""
        return self.reviews_received.count()