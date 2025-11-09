from django.contrib import admin

from .models import Task


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
        "is_moderated",
        "created_at",
    )
    list_filter = ("status", "location_type", "category", "city", "is_active", "is_moderated")
    search_fields = ("title", "description", "slug", "author__username", "moderation_comment")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
