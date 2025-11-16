# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm, CustomUserChangeForm, ComplaintForm, WarningForm, BanForm
from .models import CustomUser, UserComplaint, UserWarning, UserBan
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


@login_required
def notifications(request):
    """Страница уведомлений пользователя"""
    # Получаем предупреждения
    warnings = request.user.warnings.filter(is_active=True).select_related('admin').order_by('-created_at')
    
    # Получаем активные баны
    from django.utils import timezone
    from django.db.models import Q
    now = timezone.now()
    active_bans = request.user.bans.filter(
        is_active=True
    ).filter(
        Q(ban_until__isnull=True) | Q(ban_until__gt=now)
    ).select_related('admin').order_by('-created_at')
    
    # Получаем жалобы пользователя, которые были обработаны (есть ответ от админа)
    complaints = request.user.complaints_filed.filter(
        admin_comment__isnull=False
    ).exclude(admin_comment='').select_related('reported_user', 'admin').order_by('-updated_at')
    
    # Пагинация
    from django.core.paginator import Paginator
    all_notifications = []
    
    # Добавляем предупреждения
    for warning in warnings:
        all_notifications.append({
            'type': 'warning',
            'object': warning,
            'date': warning.created_at,
            'is_read': warning.is_read,
        })
    
    # Добавляем баны
    for ban in active_bans:
        all_notifications.append({
            'type': 'ban',
            'object': ban,
            'date': ban.created_at,
            'is_read': False,  # Баны всегда важные, считаем непрочитанными
        })
    
    # Добавляем ответы на жалобы
    for complaint in complaints:
        all_notifications.append({
            'type': 'complaint_response',
            'object': complaint,
            'date': complaint.updated_at if complaint.updated_at != complaint.created_at else complaint.created_at,
            'is_read': complaint.is_read_by_complainant,
        })
    
    # Сортируем по дате (новые сначала)
    all_notifications.sort(key=lambda x: x['date'], reverse=True)
    
    paginator = Paginator(all_notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Счетчики
    unread_count = sum(1 for n in all_notifications if not n['is_read'] and n['type'] != 'ban')
    unread_bans_count = len(active_bans)
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
        'unread_bans_count': unread_bans_count,
    }
    return render(request, 'users/notifications.html', context)


@login_required
def mark_notification_read(request, notification_type, notification_id):
    """Отметить уведомление как прочитанное"""
    if notification_type == 'warning':
        notification = get_object_or_404(UserWarning, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        messages.success(request, 'Предупреждение отмечено как прочитанное.')
    elif notification_type == 'complaint':
        notification = get_object_or_404(UserComplaint, id=notification_id, complainant=request.user)
        notification.is_read_by_complainant = True
        notification.save()
        messages.success(request, 'Ответ на жалобу отмечен как прочитанный.')
    else:
        messages.error(request, 'Неверный тип уведомления.')
    
    return redirect('users:notifications')


@login_required
def file_complaint(request, user_id=None):
    """Подача жалобы на пользователя"""
    reported_user = None
    if user_id:
        reported_user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST, user=request.user)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.complainant = request.user
            if reported_user:
                complaint.reported_user = reported_user
            complaint.save()
            messages.success(request, 'Жалоба успешно отправлена. Мы рассмотрим её в ближайшее время.')
            return redirect('users:profile')
    else:
        form = ComplaintForm(user=request.user)
        if reported_user:
            form.fields['reported_user'].initial = reported_user
    
    context = {
        'form': form,
        'reported_user': reported_user,
    }
    return render(request, 'users/file_complaint.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def moderation_panel(request):
    """Панель модерации для администраторов"""
    # Получаем жалобы
    complaints = UserComplaint.objects.all().select_related(
        'complainant', 'reported_user', 'admin'
    ).order_by('-created_at')
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        complaints = complaints.filter(status=status_filter)
    
    # Пагинация
    paginator = Paginator(complaints, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    stats = {
        'pending': UserComplaint.objects.filter(status=UserComplaint.Status.PENDING).count(),
        'reviewed': UserComplaint.objects.filter(status=UserComplaint.Status.REVIEWED).count(),
        'resolved': UserComplaint.objects.filter(status=UserComplaint.Status.RESOLVED).count(),
        'rejected': UserComplaint.objects.filter(status=UserComplaint.Status.REJECTED).count(),
        'total': UserComplaint.objects.count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
    }
    return render(request, 'users/moderation_panel.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def complaint_detail(request, complaint_id):
    """Детальная информация о жалобе"""
    complaint = get_object_or_404(UserComplaint, id=complaint_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_comment = request.POST.get('admin_comment', '')
        
        if action == 'review':
            complaint.status = UserComplaint.Status.REVIEWED
            complaint.admin = request.user
            if admin_comment:
                complaint.admin_comment = admin_comment
            complaint.save()
            messages.success(request, 'Жалоба помечена как рассмотренная.')
        elif action == 'resolve':
            complaint.status = UserComplaint.Status.RESOLVED
            complaint.admin = request.user
            if admin_comment:
                complaint.admin_comment = admin_comment
            complaint.save()
            messages.success(request, 'Жалоба помечена как решенная.')
        elif action == 'reject':
            complaint.status = UserComplaint.Status.REJECTED
            complaint.admin = request.user
            if admin_comment:
                complaint.admin_comment = admin_comment
            complaint.save()
            messages.success(request, 'Жалоба отклонена.')
        
        return redirect('users:complaint_detail', complaint_id=complaint.id)
    
    context = {
        'complaint': complaint,
    }
    return render(request, 'users/complaint_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def issue_warning(request, user_id=None):
    """Выдача предупреждения пользователю"""
    user = None
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = WarningForm(request.POST)
        if form.is_valid():
            warning = form.save(commit=False)
            warning.admin = request.user
            if user:
                warning.user = user
            warning.save()
            messages.success(request, f'Предупреждение выдано пользователю {warning.user.username}.')
            return redirect('users:moderation_panel')
    else:
        form = WarningForm()
        if user:
            form.fields['user'].initial = user
    
    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'users/issue_warning.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def issue_ban(request, user_id=None):
    """Выдача бана пользователю"""
    user = None
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = BanForm(request.POST)
        if form.is_valid():
            ban = form.save(commit=False)
            ban.admin = request.user
            if user:
                ban.user = user
            ban.save()
            ban_type = 'постоянный' if ban.is_permanent else 'временный'
            messages.success(request, f'{ban_type.capitalize()} бан выдан пользователю {ban.user.username}.')
            return redirect('users:moderation_panel')
    else:
        form = BanForm()
        if user:
            form.fields['user'].initial = user
    
    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'users/issue_ban.html', context)