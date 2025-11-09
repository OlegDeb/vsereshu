# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

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
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'date_of_birth', 'is_staff')