from django.contrib import admin
from .models import Specialty, Vacancy
from slugify import slugify as slugify_extended


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description_preview')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'description')

    def description_preview(self, obj):
        return obj.description[:100] + '...' if obj.description and len(obj.description) > 100 else obj.description


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'slug',
        'specialty',
        'experience_display',
        'employment_type_display',
        'salary',
        'city_display',
        'is_moderated',
        'is_active',
        'created_at'
    )
    list_filter = (
        'specialty',
        'experience',
        'employment_type',
        'work_nature',
        'is_moderated',
        'is_active',
        'created_at'
    )
    search_fields = ('title', 'slug', 'description', 'location', 'other_conditions')
    readonly_fields = ('created_at', 'updated_at', 'views', 'responses_count')
    list_editable = ('is_moderated', 'is_active')
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'specialty', 'author')
        }),
        ('Условия работы', {
            'fields': ('experience', 'employment_type', 'work_nature', 'other_conditions')
        }),
        ('Финансовые условия', {
            'fields': ('salary',)
        }),
        ('Местоположение', {
            'fields': ('city', 'location')
        }),
        ('Модерация', {
            'fields': ('is_moderated', 'moderation_comment')
        }),
        ('Статистика и даты', {
            'fields': ('views', 'responses_count', 'created_at', 'updated_at')
        }),
        ('Статус', {
            'fields': ('is_active',)
        })
    )

    def experience_display(self, obj):
        return dict(Vacancy.EXPERIENCE_CHOICES).get(obj.experience, obj.experience)
    experience_display.short_description = 'Опыт работы'

    def employment_type_display(self, obj):
        return dict(Vacancy.EMPLOYMENT_TYPE_CHOICES).get(obj.employment_type, obj.employment_type)
    employment_type_display.short_description = 'Тип занятости'

    def city_display(self, obj):
        if obj.city:
            return obj.city.name
        elif obj.location:
            return obj.location
        else:
            return '-'
    city_display.short_description = 'Место работы'
