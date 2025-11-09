from django.contrib import admin

from .models import Category, CategorySection


@admin.register(CategorySection)
class CategorySectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "slug", "is_active", "created_at", "updated_at")
    list_filter = ("section", "is_active")
    search_fields = ("name", "slug", "description", "short_description", "section__name")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
