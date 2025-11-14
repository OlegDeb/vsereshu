# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from tasks.models import Task, TaskResponse
from services.models import Service

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('users:profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    # Расчет количества дней с регистрации
    user_days = (timezone.now() - request.user.date_joined).days
    
    # Получаем отзывы пользователя
    from tasks.models import Review, TaskResponse
    reviews = Review.objects.filter(
        reviewed_user=request.user
    ).select_related('reviewer', 'task', 'task__author').order_by('-created_at')[:10]
    
    # Для каждого отзыва определяем, может ли текущий пользователь видеть задачу
    # В личном профиле пользователь всегда может видеть свои задачи
    for review in reviews:
        is_author = request.user == review.task.author
        is_executor = TaskResponse.objects.filter(
            task=review.task,
            candidate=request.user,
            status=TaskResponse.Status.ACCEPTED.value
        ).exists()
        review.can_view_task = is_author or is_executor or request.user.is_staff
    
    # Получаем средний рейтинг и количество отзывов
    average_rating = request.user.get_average_rating()
    reviews_count = request.user.get_reviews_count()
    
    # Статистика задач
    completed_tasks_as_author = Task.objects.filter(
        author=request.user,
        status=Task.Status.COMPLETED,
        is_active=True
    ).count()
    
    completed_tasks_as_executor = Task.objects.filter(
        responses__candidate=request.user,
        responses__status=TaskResponse.Status.ACCEPTED.value,
        status=Task.Status.COMPLETED,
        is_active=True
    ).distinct().count()
    
    active_tasks_as_author = Task.objects.filter(
        author=request.user,
        status__in=[Task.Status.OPEN, Task.Status.IN_PROGRESS, Task.Status.AWAITING_CONFIRMATION],
        is_active=True
    ).count()
    
    active_tasks_as_executor = Task.objects.filter(
        responses__candidate=request.user,
        responses__status=TaskResponse.Status.ACCEPTED.value,
        status__in=[Task.Status.IN_PROGRESS, Task.Status.AWAITING_CONFIRMATION],
        is_active=True
    ).distinct().count()
    
    # Статистика услуг
    total_services = Service.objects.filter(
        author=request.user,
        is_active=True
    ).count()
    
    moderated_services = Service.objects.filter(
        author=request.user,
        is_active=True,
        is_moderated=True
    ).count()
    
    total_services_views = Service.objects.filter(
        author=request.user,
        is_active=True
    ).aggregate(total=models.Sum('views'))['total'] or 0
    
    total_services_orders = Service.objects.filter(
        author=request.user,
        is_active=True
    ).aggregate(total=models.Sum('orders_count'))['total'] or 0
    
    context = {
        'user_days': user_days,
        'reviews': reviews,
        'average_rating': average_rating,
        'reviews_count': reviews_count,
        'completed_tasks_as_author': completed_tasks_as_author,
        'completed_tasks_as_executor': completed_tasks_as_executor,
        'active_tasks_as_author': active_tasks_as_author,
        'active_tasks_as_executor': active_tasks_as_executor,
        'total_services': total_services,
        'moderated_services': moderated_services,
        'total_services_views': total_services_views,
        'total_services_orders': total_services_orders,
    }
    return render(request, 'users/profile.html', context)


@login_required
def my_tasks(request):
    """Страница с задачами пользователя как заказчика и исполнителя"""
    # Задачи пользователя как заказчика (все его задачи)
    author_tasks = Task.objects.filter(
        author=request.user,
        is_active=True
    ).select_related("category", "city").order_by("-created_at")
    
    # Задачи пользователя как исполнителя (все задачи, где он исполнитель с принятым откликом)
    # Показываем только проверенные задачи
    executor_tasks = Task.objects.filter(
        responses__candidate=request.user,
        responses__status=TaskResponse.Status.ACCEPTED.value,
        is_active=True,
        is_moderated=True  # Исполнитель видит только проверенные задачи
    ).select_related("category", "city", "author").distinct().order_by("-created_at")
    
    # Определяем активный таб из GET параметра
    active_tab = request.GET.get('tab', 'author')  # По умолчанию показываем задачи заказчика
    
    context = {
        'author_tasks': author_tasks,
        'executor_tasks': executor_tasks,
        'active_tab': active_tab,
    }
    return render(request, 'users/my_tasks.html', context)


@login_required
def my_services(request):
    """Страница с услугами пользователя"""
    # Все услуги пользователя
    services = Service.objects.filter(
        author=request.user,
        is_active=True
    ).select_related("category", "city").order_by("-created_at")
    
    context = {
        'services': services,
    }
    return render(request, 'users/my_services.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('users:profile')
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
    
    # Получаем отзывы пользователя
    from tasks.models import Review, TaskResponse
    reviews = Review.objects.filter(
        reviewed_user=user
    ).select_related('reviewer', 'task', 'task__author').order_by('-created_at')[:10]
    
    # Для каждого отзыва определяем, может ли текущий пользователь видеть задачу
    for review in reviews:
        # Задача видна заказчику, исполнителю и администратору
        review.can_view_task = False
        if request.user.is_authenticated:
            is_author = request.user == review.task.author
            is_executor = TaskResponse.objects.filter(
                task=review.task,
                candidate=request.user,
                status=TaskResponse.Status.ACCEPTED.value
            ).exists()
            is_admin = request.user.is_staff
            review.can_view_task = is_author or is_executor or is_admin
    
    # Получаем средний рейтинг и количество отзывов
    average_rating = user.get_average_rating()
    reviews_count = user.get_reviews_count()
    
    # Статистика задач
    completed_tasks_as_author = Task.objects.filter(
        author=user,
        status=Task.Status.COMPLETED,
        is_active=True
    ).count()
    
    completed_tasks_as_executor = Task.objects.filter(
        responses__candidate=user,
        responses__status=TaskResponse.Status.ACCEPTED.value,
        status=Task.Status.COMPLETED,
        is_active=True
    ).distinct().count()
    
    active_tasks_as_author = Task.objects.filter(
        author=user,
        status__in=[Task.Status.OPEN, Task.Status.IN_PROGRESS, Task.Status.AWAITING_CONFIRMATION],
        is_active=True
    ).count()
    
    active_tasks_as_executor = Task.objects.filter(
        responses__candidate=user,
        responses__status=TaskResponse.Status.ACCEPTED.value,
        status__in=[Task.Status.IN_PROGRESS, Task.Status.AWAITING_CONFIRMATION],
        is_active=True
    ).distinct().count()
    
    # Статистика услуг
    total_services = Service.objects.filter(
        author=user,
        is_active=True
    ).count()
    
    moderated_services = Service.objects.filter(
        author=user,
        is_active=True,
        is_moderated=True
    ).count()
    
    services_views = Service.objects.filter(
        author=user,
        is_active=True
    ).aggregate(total_views=models.Sum('views'))['total_views'] or 0
    
    # Получаем список услуг пользователя (только опубликованные)
    user_services = Service.objects.filter(
        author=user,
        is_active=True,
        is_moderated=True
    ).select_related("category", "city").order_by("-created_at")[:6]
    
    context = {
        'profile_user': user,
        'user_days': user_days,
        'is_own_profile': is_own_profile,
        'reviews': reviews,
        'average_rating': average_rating,
        'reviews_count': reviews_count,
        'completed_tasks_as_author': completed_tasks_as_author,
        'completed_tasks_as_executor': completed_tasks_as_executor,
        'active_tasks_as_author': active_tasks_as_author,
        'active_tasks_as_executor': active_tasks_as_executor,
        'total_services': total_services,
        'moderated_services': moderated_services,
        'services_views': services_views,
        'user_services': user_services,
    }
    
    return render(request, 'users/public_profile.html', context)


def custom_logout(request):
    logout(request)
    return redirect('home')