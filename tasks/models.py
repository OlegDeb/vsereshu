from django.conf import settings
from django.db import models

from categories.models import Category
from regions.models import City


class Task(models.Model):
    class LocationType(models.TextChoices):
        CITY = "city", "В конкретном городе"
        REMOTE = "remote", "Удаленная работа"

    class Status(models.TextChoices):
        OPEN = "open", "Открыта"
        IN_PROGRESS = "in_progress", "В работе"
        COMPLETED = "completed", "Выполнена"
        CLOSED = "closed", "Закрыта"

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, verbose_name="URL")
    description = models.TextField(verbose_name="Описание")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Автор",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Категория",
    )
    location_type = models.CharField(
        max_length=10,
        choices=LocationType.choices,
        default=LocationType.CITY,
        verbose_name="Тип локации",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Город",
        help_text="Укажите город, если выбрана работа в городе",
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name="Статус",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активная")
    is_moderated = models.BooleanField(
        default=False,
        verbose_name="Проверена модератором",
        help_text="Отметьте, когда задача проверена модератором",
    )
    moderation_comment = models.TextField(
        blank=True,
        verbose_name="Комментарий модерации",
        help_text="Комментарий модератора по задаче",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title
