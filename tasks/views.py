from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Task, TaskResponse, Message, Review
from .forms import TaskForm, TaskResponseForm, MessageForm, ReviewForm  # type: ignore[import]
from categories.models import CategorySection, Category
from regions.models import City, Region

__all__ = ["task_list", "task_detail", "create_task", "edit_task", "create_response", "response_detail", "send_message", "update_response_status", "complete_task", "accept_task_completion", "create_review", "get_categories_by_section", "get_cities_by_region"]


def task_list(request):
    tasks = (
        Task.objects.select_related("category", "city", "author", "category__section")
        .filter(
            is_active=True,
            is_moderated=True  # Показываем только проверенные модератором задачи
        )
        .exclude(
            status__in=[Task.Status.IN_PROGRESS, Task.Status.AWAITING_CONFIRMATION, Task.Status.COMPLETED]
        )
    )
    
    # Фильтрация по разделу
    section_slug = request.GET.get("section")
    if section_slug:
        tasks = tasks.filter(category__section__slug=section_slug)
    
    # Фильтрация по категории
    category_slug = request.GET.get("category")
    selected_category_obj = None
    if category_slug:
        try:
            selected_category_obj = Category.objects.get(slug=category_slug, is_active=True)
            tasks = tasks.filter(category__slug=category_slug)
        except Category.DoesNotExist:
            pass
    
    # Фильтрация по городу
    city_id = request.GET.get("city")
    selected_city = None
    if city_id:
        try:
            selected_city = City.objects.get(pk=int(city_id), is_active=True)
            tasks = tasks.filter(city=selected_city)
        except (ValueError, City.DoesNotExist):
            pass
    
    tasks = tasks.order_by("-created_at")
    
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
    # Показываем города, которые используются в открытых задачах, или все активные города
    cities_with_tasks = City.objects.filter(
        is_active=True,
        tasks__is_active=True,
        tasks__is_moderated=True  # Только проверенные задачи
    ).exclude(
        tasks__status__in=[Task.Status.IN_PROGRESS, Task.Status.AWAITING_CONFIRMATION, Task.Status.COMPLETED]
    ).distinct()
    
    # Если есть города с задачами, показываем их, иначе показываем все активные города
    if cities_with_tasks.exists():
        cities = cities_with_tasks.select_related('region').order_by('name')
    else:
        cities = City.objects.filter(is_active=True).select_related('region').order_by('name')
    
    context = {
        "tasks": tasks,
        "sections": sections,
        "selected_section": section_slug,
        "selected_category": category_slug,
        "selected_category_obj": selected_category_obj,
        "cities": cities,
        "selected_city": selected_city,
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def create_task(request):
    """Создание новой задачи"""
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(author=request.user)
            messages.success(request, "Задача успешно создана и отправлена на модерацию!")
            return redirect("tasks:task_detail", slug=task.get_public_slug())
    else:
        form = TaskForm()
    
    return render(request, "tasks/create_task.html", {"form": form})


@login_required
def edit_task(request, slug: str):
    """Редактирование задачи"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Task not found")

    task = get_object_or_404(
        Task.objects.select_related("author"),
        pk=int(id_part),
        slug=slug_part,
    )
    
    # Проверяем, что пользователь - автор задачи
    if request.user != task.author:
        messages.error(request, "У вас нет прав для редактирования этой задачи.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Проверяем, что задача не в работе
    if task.status == Task.Status.IN_PROGRESS:
        messages.error(request, "Задачу нельзя редактировать, пока она находится в работе.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    if task.status == Task.Status.AWAITING_CONFIRMATION:
        messages.error(request, "Задачу нельзя редактировать, пока она ожидает подтверждения.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    if task.status == Task.Status.COMPLETED:
        messages.error(request, "Завершенную задачу нельзя редактировать.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            if task.is_moderated:
                messages.success(request, "Задача успешно обновлена!")
            else:
                messages.success(request, "Задача успешно обновлена и отправлена на модерацию!")
            return redirect("tasks:task_detail", slug=task.get_public_slug())
    else:
        form = TaskForm(instance=task)
    
    return render(request, "tasks/create_task.html", {"form": form, "task": task, "is_edit": True})


def task_detail(request, slug: str):
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Task not found")

    # Получаем задачу, проверяя права доступа
    task = get_object_or_404(
        Task.objects.select_related("category", "city", "author"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
    )
    
    # Если задача не проверена модератором, доступ только для автора
    if not task.is_moderated:
        if not request.user.is_authenticated or request.user != task.author:
            messages.error(request, "Эта задача находится на модерации и пока недоступна для просмотра.")
            return redirect("tasks:task_list")
    
    # Проверяем права доступа для задач в работе или выполненных
    # Такие задачи видны только заказчику, исполнителю и администратору
    if task.status in [Task.Status.IN_PROGRESS, Task.Status.AWAITING_CONFIRMATION, Task.Status.COMPLETED]:
        if not request.user.is_authenticated:
            messages.error(request, "Для просмотра этой задачи необходимо войти в систему.")
            return redirect("users:login")
        
        # Проверяем, является ли пользователь заказчиком
        is_author = request.user == task.author
        
        # Проверяем, является ли пользователь исполнителем
        is_executor_check = TaskResponse.objects.filter(
            task=task,
            candidate=request.user,
            status=TaskResponse.Status.ACCEPTED.value
        ).exists()
        
        # Проверяем, является ли пользователь администратором
        is_admin = request.user.is_staff
        
        # Если пользователь не заказчик, не исполнитель и не администратор - доступ запрещен
        if not (is_author or is_executor_check or is_admin):
            messages.error(request, "У вас нет доступа к этой задаче.")
            return redirect("tasks:task_list")
    
    # Получаем отклики на задачу
    responses = None
    user_response = None
    response_form = None
    is_executor = False
    
    if request.user.is_authenticated:
        # Если пользователь - автор задачи, показываем все отклики
        if task.author == request.user:
            responses = TaskResponse.objects.filter(
                task=task
            ).select_related("candidate").order_by("-created_at")
        # Если пользователь - не автор, проверяем, есть ли у него отклик
        else:
            user_response = TaskResponse.objects.filter(
                task=task,
                candidate=request.user
            ).first()
            if not user_response:
                response_form = TaskResponseForm()
            # Проверяем, является ли пользователь исполнителем (с принятым откликом)
            elif user_response.status == TaskResponse.Status.ACCEPTED.value:
                is_executor = True
    
    # Получаем информацию об отзывах для завершенных задач
    reviews = None
    can_review_executor = False
    can_review_author = False
    executor_review = None
    author_review = None
    
    if task.status == Task.Status.COMPLETED and request.user.is_authenticated:
        # Получаем исполнителя
        accepted_response = TaskResponse.objects.filter(
            task=task,
            status=TaskResponse.Status.ACCEPTED.value
        ).first()
        
        if accepted_response:
            # Проверяем, может ли заказчик оставить отзыв исполнителю
            if request.user == task.author:
                executor_review = Review.objects.filter(
                    task=task,
                    reviewer=request.user,
                    reviewed_user=accepted_response.candidate
                ).first()
                if not executor_review:
                    can_review_executor = True
            
            # Проверяем, может ли исполнитель оставить отзыв заказчику
            if request.user == accepted_response.candidate:
                author_review = Review.objects.filter(
                    task=task,
                    reviewer=request.user,
                    reviewed_user=task.author
                ).first()
                if not author_review:
                    can_review_author = True
        
        # Получаем все отзывы по задаче
        reviews = Review.objects.filter(
            task=task
        ).select_related('reviewer', 'reviewed_user').order_by('-created_at')
    
    context = {
        "task": task,
        "responses": responses,
        "user_response": user_response,
        "response_form": response_form,
        "is_executor": is_executor,
        "reviews": reviews,
        "can_review_executor": can_review_executor,
        "can_review_author": can_review_author,
        "executor_review": executor_review,
        "author_review": author_review,
    }
    return render(request, "tasks/task_detail.html", context)


@login_required
def create_response(request, slug: str):
    """Создание отклика на задачу"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Task not found")

    task = get_object_or_404(
        Task.objects.select_related("author"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
        is_moderated=True,  # Откликаться можно только на проверенные задачи
    )
    
    # Проверяем, что пользователь не является автором задачи
    if task.author == request.user:
        messages.error(request, "Вы не можете откликнуться на свою задачу.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Проверяем, нет ли уже отклика от этого пользователя
    existing_response = TaskResponse.objects.filter(
        task=task,
        candidate=request.user
    ).first()
    
    if existing_response:
        messages.info(request, "Вы уже откликнулись на эту задачу.")
        return redirect("tasks:response_detail", response_id=existing_response.pk)
    
    if request.method == "POST":
        form = TaskResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.task = task
            response.candidate = request.user
            response.save()
            messages.success(request, "Ваш отклик успешно отправлен!")
            return redirect("tasks:response_detail", response_id=response.pk)
    else:
        form = TaskResponseForm()
    
    return render(request, "tasks/create_response.html", {
        "task": task,
        "form": form,
    })


@login_required
def response_detail(request, response_id: int):
    """Просмотр отклика и общения"""
    response = get_object_or_404(
        TaskResponse.objects.select_related("task", "candidate", "task__author"),
        pk=response_id
    )
    
    # Проверяем права доступа: только автор задачи или кандидат могут видеть отклик
    if request.user != response.task.author and request.user != response.candidate:
        messages.error(request, "У вас нет доступа к этому отклику.")
        return redirect("tasks:task_detail", slug=response.task.get_public_slug())
    
    # Получаем все сообщения в этом отклике
    message_list = Message.objects.filter(
        task_response=response
    ).select_related("sender").order_by("created_at")
    
    # Помечаем сообщения как прочитанные для текущего пользователя
    Message.objects.filter(
        task_response=response
    ).exclude(sender=request.user).update(is_read=True)
    
    # Проверяем, является ли пользователь исполнителем (кандидатом с принятым откликом)
    is_executor = (
        request.user == response.candidate and 
        response.status == TaskResponse.Status.ACCEPTED.value
    )
    
    # Форма для отправки сообщения
    message_form = MessageForm()
    
    if request.method == "POST":
        message_form = MessageForm(request.POST)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.task_response = response
            message.sender = request.user
            message.save()
            messages.success(request, "Сообщение отправлено!")
            return redirect("tasks:response_detail", response_id=response.pk)
    
    context = {
        "response": response,
        "message_list": message_list,
        "message_form": message_form,
        "is_executor": is_executor,
    }
    return render(request, "tasks/response_detail.html", context)


@login_required
@require_POST
def send_message(request, response_id: int):
    """Отправка сообщения в рамках отклика (AJAX)"""
    response = get_object_or_404(
        TaskResponse.objects.select_related("task"),
        pk=response_id
    )
    
    # Проверяем права доступа
    if request.user != response.task.author and request.user != response.candidate:
        return JsonResponse({"error": "Нет доступа"}, status=403)
    
    form = MessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.task_response = response
        message.sender = request.user
        message.save()
        return JsonResponse({
            "success": True,
            "message": {
                "id": message.id,
                "content": message.content,
                "sender": message.sender.username,
                "created_at": message.created_at.strftime("%d.%m.%Y %H:%M"),
            }
        })
    
    return JsonResponse({"error": "Ошибка валидации"}, status=400)


@login_required
@require_POST
def update_response_status(request, response_id: int):
    """Обновление статуса отклика (принят/отклонен)"""
    response = get_object_or_404(
        TaskResponse.objects.select_related("task"),
        pk=response_id
    )
    
    # Только автор задачи может изменять статус отклика
    if request.user != response.task.author:
        messages.error(request, "У вас нет прав для изменения статуса отклика.")
        return redirect("tasks:task_detail", slug=response.task.get_public_slug())
    
    new_status = request.POST.get("status")
    if new_status in [TaskResponse.Status.ACCEPTED.value, TaskResponse.Status.REJECTED.value]:
        response.status = new_status
        response.save()
        
        # Если отклик принят, меняем статус задачи на "В работе"
        if new_status == TaskResponse.Status.ACCEPTED.value:
            task = response.task
            if task.status == Task.Status.OPEN:
                task.status = Task.Status.IN_PROGRESS
                task.save()
        
        # Получаем отображаемое значение статуса из choices
        status_display = dict(TaskResponse.Status.choices).get(new_status, new_status)
        if status_display:
            messages.success(request, f"Отклик {status_display.lower()}.")
        else:
            messages.success(request, "Статус отклика обновлен.")
    else:
        messages.error(request, "Неверный статус.")
    
    # Перенаправляем обратно на страницу общения, если пользователь был там
    # Или на страницу задачи, если нет параметра redirect_to
    redirect_to = request.POST.get("redirect_to", "task_detail")
    if redirect_to == "response_detail":
        return redirect("tasks:response_detail", response_id=response.pk)
    else:
        return redirect("tasks:task_detail", slug=response.task.get_public_slug())


@login_required
@require_POST
def complete_task(request, slug: str):
    """Завершение задачи исполнителем"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Task not found")

    task = get_object_or_404(
        Task.objects.select_related("author"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
    )
    
    # Проверяем, что пользователь - исполнитель (кандидат с принятым откликом)
    accepted_response = TaskResponse.objects.filter(
        task=task,
        candidate=request.user,
        status=TaskResponse.Status.ACCEPTED.value
    ).first()
    
    if not accepted_response:
        messages.error(request, "У вас нет прав для завершения этой задачи.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Проверяем, что задача еще не завершена и не ожидает подтверждения
    if task.status == Task.Status.COMPLETED:
        messages.info(request, "Задача уже завершена.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    if task.status == Task.Status.AWAITING_CONFIRMATION:
        messages.info(request, "Задача уже ожидает подтверждения заказчиком.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Меняем статус задачи на "Ожидает подтверждения"
    task.status = Task.Status.AWAITING_CONFIRMATION
    task.save()
    
    messages.success(request, "Задача отправлена на подтверждение заказчику!")
    return redirect("tasks:task_detail", slug=task.get_public_slug())


@login_required
@require_POST
def accept_task_completion(request, slug: str):
    """Принятие выполненной работы заказчиком"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Task not found")

    task = get_object_or_404(
        Task.objects.select_related("author"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
    )
    
    # Проверяем, что пользователь - автор задачи
    if request.user != task.author:
        messages.error(request, "У вас нет прав для принятия этой задачи.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Проверяем, что задача ожидает подтверждения
    if task.status != Task.Status.AWAITING_CONFIRMATION:
        messages.error(request, "Задача не ожидает подтверждения.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Меняем статус задачи на "Выполнена"
    task.status = Task.Status.COMPLETED
    task.save()
    
    # Получаем исполнителя (кандидата с принятым откликом)
    accepted_response = TaskResponse.objects.filter(
        task=task,
        status=TaskResponse.Status.ACCEPTED.value
    ).first()
    
    if accepted_response:
        # Проверяем, оставил ли заказчик уже отзыв
        existing_review = Review.objects.filter(
            task=task,
            reviewer=request.user,
            reviewed_user=accepted_response.candidate
        ).first()
        
        if not existing_review:
            # Перенаправляем на форму отзыва
            messages.success(request, "Работа принята! Пожалуйста, оставьте отзыв об исполнителе.")
            return redirect("tasks:create_review", slug=task.get_public_slug(), user_id=accepted_response.candidate.id)
    
    messages.success(request, "Работа принята! Задача завершена.")
    return redirect("tasks:task_detail", slug=task.get_public_slug())


@login_required
def create_review(request, slug: str, user_id: int):
    """Создание отзыва после завершения задачи"""
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Task not found")

    task = get_object_or_404(
        Task.objects.select_related("author"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
    )
    
    User = get_user_model()
    reviewed_user = get_object_or_404(
        User,
        pk=user_id
    )
    
    # Проверяем, что задача завершена
    if task.status != Task.Status.COMPLETED:
        messages.error(request, "Отзыв можно оставить только после завершения задачи.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Проверяем, что пользователь может оставить отзыв
    # Заказчик может оставить отзыв исполнителю, исполнитель - заказчику
    is_author = request.user == task.author
    is_executor = TaskResponse.objects.filter(
        task=task,
        candidate=request.user,
        status=TaskResponse.Status.ACCEPTED.value
    ).exists()
    
    if not (is_author or is_executor):
        messages.error(request, "У вас нет прав для оставления отзыва по этой задаче.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Проверяем, что reviewed_user - это либо автор (если отзыв от исполнителя), либо исполнитель (если отзыв от автора)
    if is_author:
        # Заказчик оставляет отзыв исполнителю
        accepted_response = TaskResponse.objects.filter(
            task=task,
            candidate=reviewed_user,
            status=TaskResponse.Status.ACCEPTED.value
        ).first()
        if not accepted_response:
            messages.error(request, "Неверный пользователь для отзыва.")
            return redirect("tasks:task_detail", slug=task.get_public_slug())
    else:
        # Исполнитель оставляет отзыв заказчику
        if reviewed_user != task.author:
            messages.error(request, "Неверный пользователь для отзыва.")
            return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    # Проверяем, не оставлен ли уже отзыв
    existing_review = Review.objects.filter(
        task=task,
        reviewer=request.user,
        reviewed_user=reviewed_user
    ).first()
    
    if existing_review:
        messages.info(request, "Вы уже оставили отзыв по этой задаче.")
        return redirect("tasks:task_detail", slug=task.get_public_slug())
    
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.task = task
            review.reviewer = request.user
            review.reviewed_user = reviewed_user
            review.save()
            
            # После создания отзыва проверяем, нужно ли перенаправить на создание второго отзыва
            # Если заказчик оставил отзыв, перенаправляем исполнителя на создание отзыва заказчику
            if is_author:
                # Заказчик оставил отзыв, проверяем, оставил ли исполнитель отзыв
                executor_review = Review.objects.filter(
                    task=task,
                    reviewer=reviewed_user,
                    reviewed_user=request.user
                ).first()
                if not executor_review:
                    messages.success(request, "Отзыв успешно оставлен! Теперь исполнитель может оставить отзыв о вас.")
                else:
                    messages.success(request, "Отзыв успешно оставлен!")
            else:
                # Исполнитель оставил отзыв, проверяем, оставил ли заказчик отзыв
                author_review = Review.objects.filter(
                    task=task,
                    reviewer=task.author,
                    reviewed_user=request.user
                ).first()
                if not author_review:
                    messages.success(request, "Отзыв успешно оставлен! Теперь заказчик может оставить отзыв о вас.")
                else:
                    messages.success(request, "Отзыв успешно оставлен!")
            
            return redirect("tasks:task_detail", slug=task.get_public_slug())
    else:
        form = ReviewForm()
    
    context = {
        "task": task,
        "reviewed_user": reviewed_user,
        "form": form,
    }
    return render(request, "tasks/create_review.html", context)


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
