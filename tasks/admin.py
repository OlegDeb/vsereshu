from django.contrib import admin
from django.utils.html import format_html
from slugify import slugify

from .models import Task, TaskResponse, Message, Review


@admin.action(description="Одобрить выбранные задачи")
def approve_tasks(modeladmin, request, queryset):
    """Одобрить задачи для публикации"""
    updated = queryset.update(is_moderated=True)
    modeladmin.message_user(request, f"Одобрено задач: {updated}")


@admin.action(description="Отправить выбранные задачи на модерацию")
def send_to_moderation(modeladmin, request, queryset):
    """Отправить задачи на модерацию"""
    updated = queryset.update(is_moderated=False)
    modeladmin.message_user(request, f"Отправлено на модерацию задач: {updated}")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "location_type",
        "city",
        "status",
        "is_active",
        "moderation_status",
        "views",
        "created_at",
    )
    list_filter = ("status", "location_type", "category", "city", "is_active", "is_moderated")
    search_fields = ("title", "description", "slug", "author__username", "moderation_comment")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views", "created_at", "updated_at")
    actions = [approve_tasks, send_to_moderation]
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("title", "slug", "description", "author", "category")
        }),
        ("Локация и оплата", {
            "fields": ("location_type", "city", "price", "payment_period")
        }),
        ("Статус", {
            "fields": ("status", "is_active")
        }),
        ("Статистика", {
            "fields": ("views",)
        }),
        ("Модерация", {
            "fields": ("is_moderated", "moderation_comment")
        }),
        ("Даты", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
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


@admin.register(TaskResponse)
class TaskResponseAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "candidate",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("task__title", "candidate__username", "message")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "task_response",
        "sender",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "created_at")
    search_fields = ("content", "sender__username", "task_response__task__title")
    readonly_fields = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "reviewer",
        "reviewed_user",
        "rating",
        "created_at",
    )
    list_filter = ("rating", "created_at")
    search_fields = ("comment", "reviewer__username", "reviewed_user__username", "task__title")
    readonly_fields = ("created_at",)
