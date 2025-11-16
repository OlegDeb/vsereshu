from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q, Max, Count
from django.db import models
from django.urls import reverse
from django.core.paginator import Paginator

from .models import Service, ServiceMessage
from .forms import ServiceForm, ServiceMessageForm
from categories.models import CategorySection, Category
from regions.models import City, Region


def service_list(request):
    """Список услуг"""
    services = (
        Service.objects.select_related("category", "city", "author", "category__section")
        .filter(
            is_active=True,
            is_moderated=True  # Показываем только проверенные модератором услуги
        )
    )
    
    # Фильтрация по разделу
    section_slug = request.GET.get("section")
    if section_slug:
        services = services.filter(category__section__slug=section_slug)
    
    # Фильтрация по категории
    category_slug = request.GET.get("category")
    selected_category_obj = None
    if category_slug:
        try:
            selected_category_obj = Category.objects.get(slug=category_slug, is_active=True)
            services = services.filter(category__slug=category_slug)
        except Category.DoesNotExist:
            pass
    
    # Фильтрация по городу
    city_id = request.GET.get("city")
    selected_city = None
    if city_id:
        try:
            selected_city = City.objects.get(pk=int(city_id), is_active=True)
            services = services.filter(city=selected_city)
        except (ValueError, City.DoesNotExist):
            pass
    
    # Фильтрация по автору
    author_username = request.GET.get("author")
    selected_author = None
    if author_username:
        from users.models import CustomUser
        try:
            selected_author = CustomUser.objects.get(username=author_username)
            services = services.filter(author=selected_author)
        except CustomUser.DoesNotExist:
            pass
    
    services = services.order_by("-created_at")
    
    # Пагинация
    paginator = Paginator(services, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем все активные разделы с категориями
    sections = CategorySection.objects.filter(
        is_active=True
    ).prefetch_related(
        'categories'
    ).order_by('name')
    
    # Получаем активные категории для каждого раздела
    for section in sections:
        section.categories_list = section.categories.filter(is_active=True).order_by('name')  # type: ignore[attr-defined]
    
    # Получаем все активные города
    cities_with_services = City.objects.filter(
        is_active=True,
        services__is_active=True,
        services__is_moderated=True
    ).distinct()
    
    if cities_with_services.exists():
        cities = cities_with_services.select_related('region').order_by('name')
    else:
        cities = City.objects.filter(is_active=True).select_related('region').order_by('name')
    
    context = {
        "services": page_obj,
        "page_obj": page_obj,
        "sections": sections,
        "selected_section": section_slug,
        "selected_category": category_slug,
        "selected_category_obj": selected_category_obj,
        "cities": cities,
        "selected_city": selected_city,
        "selected_author": selected_author,
    }
    return render(request, "services/service_list.html", context)


@login_required
def create_service(request):
    """Создание новой услуги"""
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(author=request.user)
            messages.success(request, "Услуга успешно создана и отправлена на модерацию!")
            return redirect("services:service_detail", slug=service.get_public_slug())
    else:
        form = ServiceForm()
    
    return render(request, "services/create_service.html", {"form": form})


@login_required
def edit_service(request, slug: str):
    """Редактирование услуги"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Service not found")

    service = get_object_or_404(
        Service.objects.select_related("author"),
        pk=int(id_part),
        slug=slug_part,
    )
    
    # Проверяем, что пользователь - автор услуги
    if request.user != service.author:
        messages.error(request, "У вас нет прав для редактирования этой услуги.")
        return redirect("services:service_detail", slug=service.get_public_slug())
    
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save()
            if service.is_moderated:
                messages.success(request, "Услуга успешно обновлена!")
            else:
                messages.success(request, "Услуга успешно обновлена и отправлена на модерацию!")
            return redirect("services:service_detail", slug=service.get_public_slug())
    else:
        form = ServiceForm(instance=service)
    
    return render(request, "services/create_service.html", {"form": form, "service": service, "is_edit": True})


def service_detail(request, slug: str):
    """Детальная страница услуги"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Service not found")

    # Получаем услугу, проверяя права доступа
    service = get_object_or_404(
        Service.objects.select_related("category", "city", "author"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
    )
    
    # Если услуга не проверена модератором, доступ только для автора
    if not service.is_moderated:
        if not request.user.is_authenticated or request.user != service.author:
            messages.error(request, "Эта услуга находится на модерации и пока недоступна для просмотра.")
            return redirect("services:service_list")
    
    # Увеличиваем счетчик просмотров
    service.views += 1
    service.save(update_fields=['views'])
    
    # Форма для отправки сообщения (только для авторизованных пользователей, которые не являются автором)
    message_form = None
    user_messages = None
    if request.user.is_authenticated and request.user != service.author:
        message_form = ServiceMessageForm()
        # Получаем переписку обычного пользователя с автором услуги
        user_messages = ServiceMessage.objects.filter(
            service=service
        ).filter(
            Q(sender=request.user, recipient=service.author) | Q(sender=service.author, recipient=request.user)
        ).select_related("sender", "recipient").order_by("created_at")
    
    # Для автора услуги получаем список диалогов (пользователей, с которыми есть переписка)
    conversations = None
    if request.user.is_authenticated and request.user == service.author:
        # Получаем уникальных пользователей, с которыми есть переписка (кроме автора)
        user_ids = ServiceMessage.objects.filter(
            service=service
        ).exclude(
            sender=service.author
        ).values_list('sender', flat=True).distinct()
        
        from users.models import CustomUser
        conversations = CustomUser.objects.filter(id__in=user_ids).annotate(
            last_message_time=Max(
                'sent_service_messages__created_at',
                filter=Q(sent_service_messages__service=service)
            ),
            unread_count=Count(
                'sent_service_messages__id',
                filter=Q(
                    sent_service_messages__service=service,
                    sent_service_messages__recipient=request.user,
                    sent_service_messages__is_read=False
                )
            )
        ).order_by('-last_message_time')
    
    context = {
        "service": service,
        "message_form": message_form,
        "conversations": conversations,
        "user_messages": user_messages,
    }
    return render(request, "services/service_detail.html", context)


def get_categories_by_section(request):
    """AJAX endpoint для получения категорий по разделу"""
    section_id = request.GET.get('section_id')
    
    if not section_id:
        return JsonResponse({'categories': []})
    
    try:
        section = CategorySection.objects.get(pk=section_id, is_active=True)
        categories = Category.objects.filter(
            section=section,
            is_active=True
        ).order_by('name').values('id', 'name')
        
        return JsonResponse({
            'categories': list(categories)
        })
    except CategorySection.DoesNotExist:
        return JsonResponse({'categories': []})


def get_cities_by_region(request):
    """AJAX endpoint для получения городов по региону"""
    region_id = request.GET.get('region_id')
    
    if not region_id:
        return JsonResponse({'cities': []})
    
    try:
        region = Region.objects.get(pk=region_id, is_active=True)
        cities = City.objects.filter(
            region=region,
            is_active=True
        ).order_by('name').values('id', 'name')
        
        return JsonResponse({
            'cities': list(cities)
        })
    except Region.DoesNotExist:
        return JsonResponse({'cities': []})


@login_required
@require_POST
def send_service_message(request, slug: str):
    """Отправка сообщения автору услуги (AJAX)"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Service not found")

    service = get_object_or_404(
        Service.objects.select_related("author"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
    )
    
    # Проверяем, что пользователь не является автором услуги
    if request.user == service.author:
        return JsonResponse({"error": "Вы не можете отправить сообщение самому себе"}, status=403)
    
    form = ServiceMessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.service = service
        message.sender = request.user
        message.recipient = service.author
        message.save()
        
        # Получаем полное имя отправителя
        sender_name = message.sender.get_full_name() or message.sender.username
        sender_avatar = message.sender.avatar.url if message.sender.avatar else None
        
        return JsonResponse({
            "success": True,
            "message": {
                "id": message.id,
                "content": message.content,
                "sender": message.sender.username,
                "sender_name": sender_name,
                "sender_avatar": sender_avatar,
                "created_at": message.created_at.strftime("%d.%m.%Y %H:%M"),
            }
        })
    
    return JsonResponse({"error": "Ошибка валидации"}, status=400)


@login_required
def service_messages(request, slug: str):
    """Просмотр диалога по услуге"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Service not found")

    service = get_object_or_404(
        Service.objects.select_related("author", "category", "city"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
    )
    
    # Получаем ID собеседника из GET параметра (для автора услуги)
    conversation_user_id = request.GET.get('user_id')
    conversation_user = None
    if conversation_user_id:
        try:
            from users.models import CustomUser
            conversation_user = CustomUser.objects.get(pk=int(conversation_user_id))
        except (ValueError, CustomUser.DoesNotExist):
            conversation_user = None
    
    # Проверяем права доступа: только автор услуги или тот, кто писал/получал сообщения, или администратор
    is_admin = request.user.is_staff
    is_author = request.user == service.author
    has_messages = False
    
    if not is_admin and not is_author:
        # Проверяем, есть ли сообщения, где пользователь является отправителем или получателем
        has_messages = ServiceMessage.objects.filter(
            service=service
        ).filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).exists()
        
        if not has_messages:
            messages.error(request, "У вас нет доступа к этому диалогу.")
            return redirect("services:service_detail", slug=service.get_public_slug())
    
    # Получаем сообщения: для обычных пользователей - только их переписка, для админов - все
    if is_admin:
        # Администратор видит все сообщения по услуге
        if conversation_user:
            # Если указан конкретный пользователь, показываем переписку с ним
            message_list = ServiceMessage.objects.filter(
                service=service
            ).filter(
                Q(sender=conversation_user) | Q(recipient=conversation_user)
            ).select_related("sender", "recipient").order_by("created_at")
        else:
            message_list = ServiceMessage.objects.filter(
                service=service
            ).select_related("sender", "recipient").order_by("created_at")
    elif is_author:
        if conversation_user:
            # Автор услуги просматривает переписку с конкретным пользователем
            message_list = ServiceMessage.objects.filter(
                service=service
            ).filter(
                Q(sender=conversation_user, recipient=request.user) | Q(sender=request.user, recipient=conversation_user)
            ).select_related("sender", "recipient").order_by("created_at")
        else:
            # Автор услуги без указания пользователя - получаем список всех диалогов для отображения
            # В этом случае message_list будет пустым, и мы покажем список диалогов
            message_list = ServiceMessage.objects.none()
    else:
        # Обычный пользователь видит только сообщения, где он отправитель или получатель
        message_list = ServiceMessage.objects.filter(
            service=service
        ).filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).select_related("sender", "recipient").order_by("created_at")
    
    # Помечаем сообщения как прочитанные для текущего пользователя
    ServiceMessage.objects.filter(
        service=service,
        recipient=request.user
    ).exclude(sender=request.user).update(is_read=True)
    
    # Определяем собеседника
    if conversation_user:
        # Если указан конкретный пользователь для диалога
        other_user = conversation_user
    elif is_author:
        # Автор услуги - находим последнего собеседника из сообщений
        last_message = message_list.exclude(sender=service.author).order_by('-created_at').first()
        other_user = last_message.sender if last_message else None
    elif is_admin:
        # Для администратора определяем собеседника из сообщений
        if request.user == service.author:
            last_message = message_list.exclude(sender=service.author).order_by('-created_at').first()
        else:
            last_message = message_list.exclude(sender=request.user).order_by('-created_at').first()
        other_user = last_message.sender if last_message else None
    else:
        # Обычный пользователь - собеседник - автор услуги
        other_user = service.author if message_list.exists() else None
    
    # Форма для отправки сообщения
    message_form = ServiceMessageForm()
    
    if request.method == "POST":
        message_form = ServiceMessageForm(request.POST)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.service = service
            message.sender = request.user
            # Определяем получателя на основе собеседника из текущего диалога
            if conversation_user:
                # Если открыт диалог с конкретным пользователем
                message.recipient = conversation_user
            elif other_user:
                message.recipient = other_user
            else:
                # Если не удалось определить собеседника, используем логику по умолчанию
                if request.user == service.author:
                    # Автор услуги - ищем последнего отправителя из отфильтрованных сообщений
                    last_message = message_list.exclude(sender=service.author).order_by('-created_at').first()
                    if last_message:
                        message.recipient = last_message.sender
                    else:
                        messages.error(request, "Не удалось определить получателя.")
                        if conversation_user:
                            return redirect(f"{reverse('services:service_messages', args=[service.get_public_slug()])}?user_id={conversation_user.id}")
                        return redirect("services:service_detail", slug=service.get_public_slug())
                else:
                    # Обычный пользователь - отправляем автору услуги
                    message.recipient = service.author
            message.save()
            messages.success(request, "Сообщение отправлено!")
            # Редиректим обратно в тот же диалог, если был указан конкретный пользователь
            if conversation_user:
                return redirect(f"{reverse('services:service_messages', args=[service.get_public_slug()])}?user_id={conversation_user.id}")
            return redirect("services:service_messages", slug=service.get_public_slug())
    
    # Для автора услуги получаем список всех диалогов, если не указан конкретный пользователь
    conversations_list = None
    if is_author and not conversation_user:
        # Получаем уникальных пользователей, с которыми есть переписка (кроме автора)
        user_ids = ServiceMessage.objects.filter(
            service=service
        ).exclude(
            sender=service.author
        ).values_list('sender', flat=True).distinct()
        
        if user_ids:
            from users.models import CustomUser
            conversations_list = CustomUser.objects.filter(id__in=user_ids).annotate(
                last_message_time=Max(
                    'sent_service_messages__created_at',
                    filter=Q(sent_service_messages__service=service)
                ),
                unread_count=Count(
                    'sent_service_messages__id',
                    filter=Q(
                        sent_service_messages__service=service,
                        sent_service_messages__recipient=request.user,
                        sent_service_messages__is_read=False
                    )
                )
            ).order_by('-last_message_time')
    
    context = {
        "service": service,
        "message_list": message_list,
        "message_form": message_form,
        "other_user": other_user,
        "conversations": conversations_list,
        "conversation_user": conversation_user,
    }
    return render(request, "services/service_messages.html", context)
