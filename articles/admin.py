from django.contrib import admin
from slugify import slugify

from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "public",
        "sidebar",
        "create_at",
    )
    list_filter = ("category", "public", "sidebar", "create_at")
    search_fields = ("title", "slug", "description", "text")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("create_at",)
    autocomplete_fields = ("category",)
    ordering = ("-create_at",)
