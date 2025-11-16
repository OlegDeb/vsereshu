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
    
    def is_banned(self):
        """Проверяет, забанен ли пользователь (временно или постоянно)"""
        from django.utils import timezone
        from django.db.models import Q
        now = timezone.now()
        # Проверяем активные баны
        active_bans = self.bans.filter(
            is_active=True
        ).filter(
            Q(ban_until__isnull=True) | Q(ban_until__gt=now)
        )
        return active_bans.exists()
    
    def get_active_ban(self):
        """Возвращает активный бан пользователя, если есть"""
        from django.utils import timezone
        from django.db.models import Q
        now = timezone.now()
        return self.bans.filter(
            is_active=True
        ).filter(
            Q(ban_until__isnull=True) | Q(ban_until__gt=now)
        ).first()
    
    def get_warnings_count(self):
        """Возвращает количество активных предупреждений"""
        return self.warnings.filter(is_active=True).count()


class UserWarning(models.Model):
    """Предупреждение пользователю от администратора"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='warnings',
        verbose_name="Пользователь"
    )
    admin = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='warnings_issued',
        verbose_name="Администратор",
        limit_choices_to={'is_staff': True}
    )
    reason = models.TextField(verbose_name="Причина предупреждения")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Предупреждение"
        verbose_name_plural = "Предупреждения"
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"Предупреждение для {self.user.username} от {self.created_at.strftime('%d.%m.%Y')}"


class UserBan(models.Model):
    """Бан пользователя (временный или постоянный)"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='bans',
        verbose_name="Пользователь"
    )
    admin = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bans_issued',
        verbose_name="Администратор",
        limit_choices_to={'is_staff': True}
    )
    reason = models.TextField(verbose_name="Причина бана")
    ban_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Бан до",
        help_text="Оставьте пустым для постоянного бана"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Бан"
        verbose_name_plural = "Баны"
        ordering = ('-created_at',)
    
    def __str__(self):
        if self.ban_until:
            return f"Временный бан для {self.user.username} до {self.ban_until.strftime('%d.%m.%Y %H:%M')}"
        return f"Постоянный бан для {self.user.username}"
    
    @property
    def is_permanent(self):
        """Проверяет, является ли бан постоянным"""
        return self.ban_until is None
    
    def is_expired(self):
        """Проверяет, истек ли временный бан"""
        if self.is_permanent:
            return False
        from django.utils import timezone
        return timezone.now() > self.ban_until


class UserComplaint(models.Model):
    """Жалоба пользователя на другого пользователя"""
    class ComplaintType(models.TextChoices):
        SPAM = "spam", "Спам"
        INAPPROPRIATE_BEHAVIOR = "inappropriate", "Непристойное поведение"
        FRAUD = "fraud", "Мошенничество"
        OTHER = "other", "Другое"
    
    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        REVIEWED = "reviewed", "Рассмотрена"
        RESOLVED = "resolved", "Решена"
        REJECTED = "rejected", "Отклонена"
    
    complainant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='complaints_filed',
        verbose_name="Подавший жалобу"
    )
    reported_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='complaints_received',
        verbose_name="На кого пожаловались"
    )
    complaint_type = models.CharField(
        max_length=20,
        choices=ComplaintType.choices,
        verbose_name="Тип жалобы"
    )
    description = models.TextField(verbose_name="Описание проблемы")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус"
    )
    admin_comment = models.TextField(
        blank=True,
        verbose_name="Комментарий администратора"
    )
    admin = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints_processed',
        verbose_name="Обработавший администратор",
        limit_choices_to={'is_staff': True}
    )
    is_read_by_complainant = models.BooleanField(
        default=False,
        verbose_name="Прочитано подавшим жалобу"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Жалоба"
        verbose_name_plural = "Жалобы"
        ordering = ('-created_at',)
        # Убрали unique_together с created_at, так как это может вызвать проблемы
        # Можно добавить ограничение на уровне базы данных, если нужно предотвратить дубликаты
    
    def __str__(self):
        return f"Жалоба от {self.complainant.username} на {self.reported_user.username} ({self.get_complaint_type_display()})"