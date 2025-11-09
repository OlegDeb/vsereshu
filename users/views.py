# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    # Расчет количества дней с регистрации
    user_days = (timezone.now() - request.user.date_joined).days
    return render(request, 'users/profile.html', {'user_days': user_days})

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    return render(request, 'users/profile_edit.html', {'form': form})


def public_profile(request, username):
    # Получаем пользователя или 404
    user = get_object_or_404(CustomUser, username=username)
    
    # Расчет количества дней с регистрации
    user_days = (timezone.now() - user.date_joined).days
    
    # Проверяем, является ли это профилем текущего пользователя
    is_own_profile = request.user.is_authenticated and request.user == user
    
    context = {
        'profile_user': user,
        'user_days': user_days,
        'is_own_profile': is_own_profile,
    }
    
    return render(request, 'users/public_profile.html', context)


def custom_logout(request):
    logout(request)
    return redirect('home')