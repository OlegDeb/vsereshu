from django.db.models import Q, Count, Max
from tasks.models import Message, TaskResponse, Task
from services.models import ServiceMessage
from regions.models import City
from categories.models import CategorySection


def unread_messages(request):
    """Context processor для непрочитанных сообщений в навбаре"""
    if not request.user.is_authenticated:
        return {
            'unread_messages_count': 0,
            'unread_messages_list': []
        }
    
    user = request.user
    
    # Получаем непрочитанные сообщения по задачам
    # Для автора задачи: сообщения от кандидатов в его задачах
    # Для кандидата: сообщения от автора задачи в его откликах
    unread_task_messages = Message.objects.filter(
        is_read=False
    ).exclude(
        sender=user
    ).select_related(
        'task_response__task',
        'task_response__candidate',
        'sender'
    )
    
    # Фильтруем: только сообщения, где пользователь является автором задачи или кандидатом
    unread_task_messages = unread_task_messages.filter(
        Q(task_response__task__author=user) | Q(task_response__candidate=user)
    )
    
    # Получаем непрочитанные сообщения по услугам
    # Сообщения, где текущий пользователь - получатель
    unread_service_messages = ServiceMessage.objects.filter(
        recipient=user,
        is_read=False
    ).select_related(
        'service',
        'sender'
    )
    
    # Подготавливаем список сообщений для отображения
    messages_list = []
    
    # Группируем сообщения по задачам (по response_id)
    task_messages_dict = {}
    for msg in unread_task_messages.order_by('-created_at')[:20]:
        task_response = msg.task_response
        task = task_response.task
        other_user = task.author if user == task_response.candidate else task_response.candidate
        
        # Создаем уникальный ключ для response
        key = f'task_response_{task_response.id}'
        
        if key not in task_messages_dict:
            task_messages_dict[key] = {
                'type': 'task',
                'task': task,
                'task_response': task_response,
                'other_user': other_user,
                'last_message': msg,
                'unread_count': 1,
                'url': f'/tasks/responses/{task_response.id}/',
            }
        else:
            task_messages_dict[key]['unread_count'] += 1
            if msg.created_at > task_messages_dict[key]['last_message'].created_at:
                task_messages_dict[key]['last_message'] = msg
    
    # Группируем сообщения по услугам
    service_messages_dict = {}
    for msg in unread_service_messages.order_by('-created_at')[:20]:
        service = msg.service
        other_user = msg.sender
        
        # Создаем уникальный ключ для услуги и пользователя
        key = f'service_{service.id}_{other_user.id}'
        
        if key not in service_messages_dict:
            service_messages_dict[key] = {
                'type': 'service',
                'service': service,
                'other_user': other_user,
                'last_message': msg,
                'unread_count': 1,
                'url': f'/services/{service.slug}/messages/?user_id={other_user.id}',
            }
        else:
            service_messages_dict[key]['unread_count'] += 1
            if msg.created_at > service_messages_dict[key]['last_message'].created_at:
                service_messages_dict[key]['last_message'] = msg
    
    # Объединяем и сортируем по дате последнего сообщения
    all_messages = list(task_messages_dict.values()) + list(service_messages_dict.values())
    all_messages.sort(
        key=lambda x: x['last_message'].created_at,
        reverse=True
    )
    
    # Берем последние 10 для отображения
    messages_list = all_messages[:10]
    
    # Общий счетчик непрочитанных
    total_unread_count = len(task_messages_dict) + len(service_messages_dict)
    
    return {
        'unread_messages_count': total_unread_count,
        'unread_messages_list': messages_list
    }


def footer_data(request):
    """Context processor для данных футера"""
    # Получаем активные города (топ 10 для футера)
    footer_cities = City.objects.filter(
        is_active=True
    ).select_related('region').order_by('name')[:10]
    
    # Получаем активные разделы категорий
    footer_sections = CategorySection.objects.filter(
        is_active=True
    ).prefetch_related(
        'categories'
    ).order_by('name')[:6]
    
    # Для каждого раздела получаем активные категории
    for section in footer_sections:
        section.footer_categories = section.categories.filter(is_active=True).order_by('name')[:5]
    
    # Получаем последние статьи
    try:
        from articles.models import Article
        footer_articles = Article.objects.filter(
            public=True
        ).select_related('category').order_by('-create_at')[:5]
    except ImportError:
        footer_articles = []
    
    return {
        'footer_cities': footer_cities,
        'footer_sections': footer_sections,
        'footer_articles': footer_articles,
    }

