from django.conf import settings
from django.db import models
from django.urls import reverse

from categories.models import Category
from regions.models import City


class Service(models.Model):
    class LocationType(models.TextChoices):
        REMOTE = "remote", "Удаленно"
        CUSTOMER = "customer", "У заказчика"
        SELF = "self", "У себя"

    class PaymentPeriod(models.TextChoices):
        FIXED = "fixed", "За услугу"
        HOUR = "hour", "За час"
        DAY = "day", "За день"
        MONTH = "month", "За месяц"

    title = models.CharField(max_length=200, verbose_name="Название услуги")
    slug = models.SlugField(unique=True, verbose_name="URL")
    description = models.TextField(verbose_name="Описание услуги")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Автор",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Категория",
    )
    location_type = models.CharField(
        max_length=10,
        choices=LocationType.choices,
        default=LocationType.REMOTE,
        verbose_name="Место оказания услуги",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
        verbose_name="Город",
        help_text="Укажите город для работы у себя или у заказчика",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Стоимость услуги",
        help_text="Укажите стоимость услуги",
    )
    payment_period = models.CharField(
        max_length=10,
        choices=PaymentPeriod.choices,
        default=PaymentPeriod.FIXED,
        verbose_name="Период для стоимости",
        help_text="Выберите период оплаты",
    )
    is_active = models.BooleanField(default=True, verbose_name="Показывать услугу")
    is_moderated = models.BooleanField(
        default=False,
        verbose_name="Проверена модератором",
        help_text="Отметьте, когда услуга проверена модератором",
    )
    moderation_comment = models.TextField(
        blank=True,
        verbose_name="Комментарий модерации",
        help_text="Комментарий модератора по услуге",
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество просмотров"
    )
    orders_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество заказов"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата размещения")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата редактирования услуги")

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("services:service_detail", args=(self.slug,))


class ServiceMessage(models.Model):
    """Сообщение между автором услуги и потенциальным заказчиком"""
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Услуга",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_service_messages",
        verbose_name="Отправитель",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_service_messages",
        verbose_name="Получатель",
    )
    content = models.TextField(verbose_name="Содержание")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Сообщение по услуге"
        verbose_name_plural = "Сообщения по услугам"
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"Сообщение от {self.sender.username} по услуге {self.service.title}"
