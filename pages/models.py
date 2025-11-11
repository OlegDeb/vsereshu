from django.db import models
from django.utils.text import slugify


class Page(models.Model):
    """Модель для статических страниц (политика конфиденциальности, правила сайта и т.д.)"""
    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок",
        help_text="Заголовок страницы"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="URL-адрес",
        help_text="Уникальный URL-адрес страницы (например: privacy-policy)"
    )
    content = models.TextField(
        verbose_name="Содержание",
        help_text="Текст страницы"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
        help_text="Отображать ли страницу на сайте"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
