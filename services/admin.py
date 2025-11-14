from django.contrib import admin
from django.utils.html import format_html
from .models import Service, ServiceMessage


@admin.action(description="Одобрить выбранные услуги")
def approve_services(modeladmin, request, queryset):
    """Одобрить услуги для публикации"""
    updated = queryset.update(is_moderated=True)
    modeladmin.message_user(request, f"Одобрено услуг: {updated}")


@admin.action(description="Отправить выбранные услуги на модерацию")
def send_to_moderation(modeladmin, request, queryset):
    """Отправить услуги на модерацию"""
    updated = queryset.update(is_moderated=False)
    modeladmin.message_user(request, f"Отправлено на модерацию услуг: {updated}")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'location_type', 'price', 'payment_period', 'is_active', 'moderation_status', 'views', 'orders_count', 'created_at')
    list_filter = ('is_active', 'is_moderated', 'location_type', 'payment_period', 'category', 'created_at')
    search_fields = ('title', 'description', 'slug', 'author__username', 'author__email', 'moderation_comment')
    readonly_fields = ('views', 'orders_count', 'created_at', 'updated_at')
    prepopulated_fields = {"slug": ("title",)}
    actions = [approve_services, send_to_moderation]
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'author', 'category')
        }),
        ('Местоположение и стоимость', {
            'fields': ('location_type', 'city', 'price', 'payment_period')
        }),
        ('Статистика', {
            'fields': ('views', 'orders_count')
        }),
        ('Модерация', {
            'fields': ('is_active', 'is_moderated', 'moderation_comment')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    @admin.display(description="Статус модерации")
    def moderation_status(self, obj):
        """Отображает статус модерации с цветом"""
        if obj.is_moderated:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Проверена</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ На модерации</span>'
            )


@admin.register(ServiceMessage)
class ServiceMessageAdmin(admin.ModelAdmin):
    list_display = (
        "service",
        "sender",
        "recipient",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "created_at")
    search_fields = ("content", "sender__username", "recipient__username", "service__title")
    readonly_fields = ("created_at",)
