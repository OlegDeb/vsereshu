# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import CustomUser, UserWarning, UserBan, UserComplaint

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Просто указываем поля только для чтения
    readonly_fields = ('date_joined', 'last_login')
    
    # Добавляем дополнительные поля к стандартным
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('date_of_birth', 'phone_number', 'gender', 'bio', 'avatar')
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'date_of_birth', 'is_staff', 'ban_status')
    
    def ban_status(self, obj):
        if obj.is_banned():
            ban = obj.get_active_ban()
            if ban and ban.is_permanent:
                return format_html('<span style="color: red;">🔴 Постоянный бан</span>')
            elif ban:
                return format_html('<span style="color: orange;">🟠 Временный бан до {}</span>', ban.ban_until.strftime('%d.%m.%Y %H:%M'))
        warnings = obj.get_warnings_count()
        if warnings > 0:
            return format_html('<span style="color: yellow;">⚠️ {} предупреждений</span>', warnings)
        return format_html('<span style="color: green;">✅ OK</span>')
    ban_status.short_description = 'Статус'


@admin.register(UserWarning)
class UserWarningAdmin(admin.ModelAdmin):
    list_display = ('user', 'admin', 'reason_short', 'is_active', 'is_read', 'created_at')
    list_filter = ('is_active', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'reason')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'admin', 'reason', 'is_active', 'is_read')
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def reason_short(self, obj):
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Причина'
    
    def save_model(self, request, obj, form, change):
        if not change:  # При создании
            obj.admin = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    list_display = ('user', 'admin', 'ban_type', 'ban_until', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'ban_until')
    search_fields = ('user__username', 'user__email', 'reason')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'admin', 'reason', 'ban_until', 'is_active')
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def ban_type(self, obj):
        if obj.is_permanent:
            return 'Постоянный'
        return 'Временный'
    ban_type.short_description = 'Тип бана'
    
    def save_model(self, request, obj, form, change):
        if not change:  # При создании
            obj.admin = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserComplaint)
class UserComplaintAdmin(admin.ModelAdmin):
    list_display = ('complainant', 'reported_user', 'complaint_type', 'status', 'is_read_by_complainant', 'created_at', 'admin')
    list_filter = ('status', 'complaint_type', 'is_read_by_complainant', 'created_at')
    search_fields = ('complainant__username', 'reported_user__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('complainant', 'reported_user', 'complaint_type', 'description', 'status')
        }),
        ('Обработка', {
            'fields': ('admin', 'admin_comment', 'is_read_by_complainant')
        }),
        ('Дополнительно', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and obj.status != UserComplaint.Status.PENDING and not obj.admin:
            obj.admin = request.user
        super().save_model(request, obj, form, change)