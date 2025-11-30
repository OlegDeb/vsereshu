from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings
from slugify import slugify as slugify_extended
from regions.models import City


class Specialty(models.Model):
    """Модель специальности"""
    name = models.CharField(max_length=200, verbose_name="Название специальности")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Слаг")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('vacancies:specialty_detail', kwargs={'slug': self.slug})


class Vacancy(models.Model):
    """Модель вакансии"""
    
    EXPERIENCE_CHOICES = [
        ('no_experience', 'Без опыта'),
        ('less_than_year', 'Меньше года'),
        ('more_than_year', 'Больше года'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Полная занятость'),
        ('part_time', 'Частичная занятость'),
        ('remote', 'Удаленная работа'),
    ]
    
    WORK_NATURE_CHOICES = [
        ('on_site', 'На точке'),
        ('office', 'В офисе'),
        ('traveling', 'Разъездная'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название вакансии")
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="Слаг")
    description = models.TextField(verbose_name="Описание вакансии")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vacancies',
        verbose_name="Автор",
        null=True,
        default=1
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.CASCADE,
        related_name='vacancies',
        verbose_name="Специальность"
    )
    experience = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        verbose_name="Опыт работы"
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name="Тип занятости"
    )
    work_nature = models.CharField(
        max_length=20,
        choices=WORK_NATURE_CHOICES,
        verbose_name="Характер работы"
    )
    other_conditions = models.TextField(blank=True, verbose_name="Другие условия")
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Зарплата",
        help_text="Укажите зарплату в рублях"
    )
    location = models.CharField(max_length=200, verbose_name="Место работы", blank=True)
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacancies',
        verbose_name="Город"
    )
    is_moderated = models.BooleanField(
        default=False,
        verbose_name="Проверена модератором",
        help_text="Отметьте, когда вакансия проверена модератором"
    )
    moderation_comment = models.TextField(
        blank=True,
        verbose_name="Комментарий модерации",
        help_text="Комментарий модератора по вакансии"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")
    responses_count = models.PositiveIntegerField(default=0, verbose_name="Количество откликов")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['specialty']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_moderated']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return f"{self.title} - {self.specialty.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify_extended(self.title)
            slug = base_slug
            counter = 1
            while Vacancy.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('vacancies:vacancy_detail', kwargs={'slug': self.slug})


class VacancyResponse(models.Model):
    """Модель отклика на вакансию"""
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name="Вакансия"
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vacancy_responses',
        verbose_name="Соискатель"
    )
    cover_letter = models.TextField(verbose_name="Сопроводительное письмо")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отклика")

    class Meta:
        verbose_name = "Отклик на вакансию"
        verbose_name_plural = "Отклики на вакансии"
        ordering = ['-created_at']
        unique_together = ['vacancy', 'applicant']

    def __str__(self):
        return f"Отклик от {self.applicant.username} на вакансию {self.vacancy.title}"


class FavoriteVacancy(models.Model):
    """Модель избранных вакансий"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_vacancies',
        verbose_name="Пользователь"
    )
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name="Вакансия"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Избранная вакансия"
        verbose_name_plural = "Избранные вакансии"
        ordering = ['-created_at']
        unique_together = ['user', 'vacancy']

    def __str__(self):
        return f"{self.user.username} - {self.vacancy.title}"
