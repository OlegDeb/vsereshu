from django.contrib import admin

from .models import City, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "slug", "is_active")
    list_filter = ("region", "is_active")
    search_fields = ("name", "slug", "region__name")
    prepopulated_fields = {"slug": ("name",)}