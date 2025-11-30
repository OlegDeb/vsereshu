# users/context_processors.py
from django.utils import timezone
from django.db.models import Q
from .models import UserWarning, UserBan, UserComplaint
from vacancies.models import VacancyResponse


def notifications(request):
    """Context processor для уведомлений в навбаре"""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
        }
    
    user = request.user
    
    # Получаем непрочитанные предупреждения
    unread_warnings_count = UserWarning.objects.filter(
        user=user,
        is_active=True,
        is_read=False
    ).count()
    
    # Получаем активные баны (считаем важными)
    now = timezone.now()
    active_bans_count = UserBan.objects.filter(
        user=user,
        is_active=True
    ).filter(
        Q(ban_until__isnull=True) | Q(ban_until__gt=now)
    ).count()
    
    # Получаем непрочитанные ответы на жалобы
    unread_complaint_responses_count = UserComplaint.objects.filter(
        complainant=user,
        admin_comment__isnull=False
    ).exclude(admin_comment='').filter(
        is_read_by_complainant=False
    ).count()
    
    # Получаем непрочитанные отклики на вакансии пользователя
    unread_vacancy_responses_count = VacancyResponse.objects.filter(
        vacancy__author=user,
        is_read=False
    ).count()
    
    # Общее количество непрочитанных уведомлений
    total_count = unread_warnings_count + active_bans_count + unread_complaint_responses_count + unread_vacancy_responses_count
    
    return {
        'unread_notifications_count': total_count,
        'unread_vacancy_responses_count': unread_vacancy_responses_count,
    }

