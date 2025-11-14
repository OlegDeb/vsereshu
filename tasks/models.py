from django.conf import settings
from django.db import models
from django.urls import reverse

from categories.models import Category
from regions.models import City


class Task(models.Model):
    class LocationType(models.TextChoices):
        SELF = "self", "У себя"
        REMOTE = "remote", "Удаленно"
        CUSTOMER = "customer", "У заказчика"

    class Status(models.TextChoices):
        OPEN = "open", "Открыта"
        IN_PROGRESS = "in_progress", "В работе"
        AWAITING_CONFIRMATION = "awaiting_confirmation", "Ожидает подтверждения"
        COMPLETED = "completed", "Выполнена"
        CLOSED = "closed", "Закрыта"

    class PaymentPeriod(models.TextChoices):
        FIXED = "fixed", "Под ключ"
        HOUR = "hour", "За час"
        DAY = "day", "За день"
        MONTH = "month", "За месяц"

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
        default=LocationType.CUSTOMER,
        verbose_name="Место выполнения задачи",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Город",
        help_text="Укажите город для работы у себя или у заказчика",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Стоимость",
        help_text="Укажите стоимость работы",
    )
    payment_period = models.CharField(
        max_length=10,
        choices=PaymentPeriod.choices,
        default=PaymentPeriod.FIXED,
        verbose_name="Период оплаты",
        help_text="Выберите период оплаты",
    )
    status = models.CharField(
        max_length=25,
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
    views = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество просмотров"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title

    def get_public_slug(self) -> str:
        return f"{self.pk}-{self.slug}"

    def get_absolute_url(self) -> str:
        return reverse("tasks:task_detail", args=(self.get_public_slug(),))


class TaskResponse(models.Model):
    """Отклик на задачу от кандидата"""
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает рассмотрения"
        ACCEPTED = "accepted", "Принят"
        REJECTED = "rejected", "Отклонен"
        WITHDRAWN = "withdrawn", "Отозван"

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Задача",
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_responses",
        verbose_name="Кандидат",
    )
    message = models.TextField(
        verbose_name="Сообщение",
        help_text="Ваше сообщение автору задачи",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        verbose_name = "Отклик на задачу"
        verbose_name_plural = "Отклики на задачи"
        ordering = ("-created_at",)
        unique_together = [["task", "candidate"]]

    def __str__(self) -> str:
        return f"Отклик от {self.candidate.username} на задачу {self.task.title}"


class Message(models.Model):
    """Сообщение между автором задачи и кандидатом"""
    task_response = models.ForeignKey(
        TaskResponse,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Отклик",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name="Отправитель",
    )
    content = models.TextField(verbose_name="Содержание")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"Сообщение от {self.sender.username} в отклике #{self.task_response.id}"


class Review(models.Model):
    """Отзыв и рейтинг между пользователями после завершения задачи"""
    RATING_CHOICES = [
        (1, "1 - Очень плохо"),
        (2, "2 - Плохо"),
        (3, "3 - Удовлетворительно"),
        (4, "4 - Хорошо"),
        (5, "5 - Отлично"),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Задача",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_given",
        verbose_name="Автор отзыва",
    )
    reviewed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_received",
        verbose_name="Получатель отзыва",
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name="Рейтинг",
        help_text="Оцените работу от 1 до 5",
    )
    comment = models.TextField(
        verbose_name="Отзыв",
        help_text="Оставьте отзыв о работе",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ("-created_at",)
        unique_together = [["task", "reviewer"]]
        indexes = [
            models.Index(fields=["reviewed_user", "-created_at"]),
        ]
    
    def __str__(self) -> str:
        return f"Отзыв от {self.reviewer.username} для {self.reviewed_user.username} по задаче {self.task.title}"
    
    def get_reviewer_role(self):
        """Определяет роль автора отзыва: заказчик или исполнитель"""
        if self.reviewer == self.task.author:
            return "заказчик"
        else:
            return "исполнитель"
    
    def get_reviewed_user_role(self):
        """Определяет роль оцениваемого пользователя: заказчик или исполнитель"""
        if self.reviewed_user == self.task.author:
            return "заказчик"
        else:
            return "исполнитель"
    
    def get_review_description(self):
        """Возвращает понятное описание отзыва"""
        if self.reviewer == self.task.author:
            # Заказчик оценил исполнителя
            return "Заказчик оценил работу исполнителя"
        else:
            # Исполнитель оценил заказчика
            return "Исполнитель оценил заказчика"
