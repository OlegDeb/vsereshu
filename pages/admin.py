from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active", "created_at", "updated_at"]
    search_fields = ["title", "slug", "content"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("title", "slug", "is_active")
        }),
        ("Содержание", {
            "fields": ("content",)
        }),
        ("Даты", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

