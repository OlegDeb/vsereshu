from django.db import models



class CategorySection(models.Model):
    """Раздел категорий (верхний уровень)"""
    
    name = models.CharField(max_length=100, verbose_name="Название раздела")
    slug = models.SlugField(unique=True, verbose_name="URL")
    icon = models.CharField(max_length=50, verbose_name="Иконка", help_text="Название класса иконки (например: 'fas fa-tools', 'bi-house')")
    description = models.TextField(max_length=500, verbose_name="SEO описание", help_text="Описание для поисковых систем (максимум 500 символов)", blank=True)
    short_description = models.CharField(max_length=200, verbose_name="Краткое описание", help_text="Короткое описание для карточек", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        verbose_name = "Раздел категорий"
        verbose_name_plural = "Разделы категорий"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(unique=True, verbose_name="URL")
    section = models.ForeignKey(CategorySection, on_delete=models.CASCADE, related_name='categories', verbose_name="Раздел")
    description = models.TextField(verbose_name="Описание", help_text="Подробное описание категории", blank=True)
    short_description = models.CharField(max_length=200, verbose_name="Краткое описание", help_text="Короткое описание для карточек", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активная")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return f"{self.section.name} → {self.name}"

