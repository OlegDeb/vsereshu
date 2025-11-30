from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.urls import reverse

from .models import Vacancy, VacancyResponse, Specialty, FavoriteVacancy
from .forms import VacancyForm, VacancyResponseForm
from regions.models import City, Region


def vacancy_list(request):
    """Список вакансий"""
    vacancies = (
        Vacancy.objects.select_related("specialty", "author", "city", "city__region")
        .filter(
            is_active=True,
            is_moderated=True  # Показываем только проверенные модератором вакансии
        )
    )
    
    # Поиск по названию и описанию
    search_query = request.GET.get("search")
    if search_query:
        vacancies = vacancies.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Фильтрация по специальности
    specialty_slug = request.GET.get("specialty")
    selected_specialty = None
    if specialty_slug:
        try:
            selected_specialty = Specialty.objects.get(slug=specialty_slug)
            vacancies = vacancies.filter(specialty__slug=specialty_slug)
        except Specialty.DoesNotExist:
            pass
    
    # Фильтрация по опыту работы
    experience = request.GET.get("experience")
    if experience:
        vacancies = vacancies.filter(experience=experience)
    
    # Фильтрация по типу занятости
    employment_type = request.GET.get("employment_type")
    if employment_type:
        vacancies = vacancies.filter(employment_type=employment_type)
    
    # Фильтрация по автору
    author_username = request.GET.get("author")
    selected_author = None
    if author_username:
        from users.models import CustomUser
        try:
            selected_author = CustomUser.objects.get(username=author_username)
            vacancies = vacancies.filter(author=selected_author)
        except CustomUser.DoesNotExist:
            pass
    
    # Сортировка
    sort_by = request.GET.get("sort", "-created_at")
    if sort_by in ["-created_at", "created_at", "-salary", "salary", "-views", "views"]:
        vacancies = vacancies.order_by(sort_by)
    else:
        vacancies = vacancies.order_by("-created_at")
    
    # Пагинация
    paginator = Paginator(vacancies, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем все специальности
    specialties = Specialty.objects.all().order_by('name')
    
    context = {
        "vacancies": page_obj,
        "page_obj": page_obj,
        "specialties": specialties,
        "selected_specialty": selected_specialty,
        "selected_experience": experience,
        "selected_employment_type": employment_type,
        "selected_author": selected_author,
        "experience_choices": Vacancy.EXPERIENCE_CHOICES,
        "employment_type_choices": Vacancy.EMPLOYMENT_TYPE_CHOICES,
    }
    return render(request, "vacancies/vacancy_list.html", context)


@login_required
def create_vacancy(request):
    """Создание новой вакансии"""
    if request.method == "POST":
        form = VacancyForm(request.POST)
        if form.is_valid():
            vacancy = form.save(author=request.user)
            messages.success(request, "Вакансия успешно создана и отправлена на модерацию!")
            return redirect("vacancies:vacancy_detail", slug=vacancy.slug)
    else:
        form = VacancyForm()
    
    return render(request, "vacancies/create_vacancy.html", {"form": form})


@login_required
def edit_vacancy(request, slug: str):
    """Редактирование вакансии"""
    vacancy = get_object_or_404(
        Vacancy.objects.select_related("author"),
        slug=slug,
    )
    
    # Проверяем, что пользователь - автор вакансии
    if request.user != vacancy.author:
        messages.error(request, "У вас нет прав для редактирования этой вакансии.")
        return redirect("vacancies:vacancy_detail", slug=vacancy.slug)
    
    if request.method == "POST":
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            vacancy = form.save()
            if vacancy.is_moderated:
                messages.success(request, "Вакансия успешно обновлена!")
            else:
                messages.success(request, "Вакансия успешно обновлена и отправлена на модерацию!")
            return redirect("vacancies:vacancy_detail", slug=vacancy.slug)
    else:
        form = VacancyForm(instance=vacancy)
    
    return render(request, "vacancies/edit_vacancy.html", {"form": form, "vacancy": vacancy})


def vacancy_detail(request, slug: str):
    """Детальная страница вакансии"""
    # Получаем вакансию по слаг
    vacancy = get_object_or_404(
        Vacancy.objects.select_related("specialty", "author"),
        slug=slug,
        is_active=True,
    )
    
    # Если вакансия не проверена модератором, доступ только для автора
    if not vacancy.is_moderated:
        if not request.user.is_authenticated or request.user != vacancy.author:
            messages.error(request, "Эта вакансия находится на модерации и пока недоступна для просмотра.")
            return redirect("vacancies:vacancy_list")
    
    # Увеличиваем счетчик просмотров
    vacancy.views += 1
    vacancy.save(update_fields=['views'])
    
    # Форма для отклика (только для авторизованных пользователей, которые не являются автором)
    response_form = None
    user_has_responded = False
    is_favorite = False
    
    if request.user.is_authenticated:
        if request.user != vacancy.author:
            response_form = VacancyResponseForm()
            # Проверяем, откликался ли уже пользователь
            user_has_responded = VacancyResponse.objects.filter(
                vacancy=vacancy, applicant=request.user
            ).exists()
        
        # Проверяем, добавлена ли вакансия в избранное
        is_favorite = FavoriteVacancy.objects.filter(
            user=request.user, vacancy=vacancy
        ).exists()
    
    # Для автора вакансии получаем список откликов
    responses = None
    new_responses_count = 0
    if request.user.is_authenticated and request.user == vacancy.author:
        responses = VacancyResponse.objects.filter(
            vacancy=vacancy
        ).select_related("applicant").order_by("-created_at")
        
        # Считаем непрочитанные отклики
        new_responses_count = responses.filter(is_read=False).count()
    
    # Похожие вакансии (той же специальности, кроме текущей)
    similar_vacancies = Vacancy.objects.filter(
        specialty=vacancy.specialty,
        is_active=True,
        is_moderated=True
    ).exclude(pk=vacancy.pk).select_related("specialty", "author", "city", "city__region")[:5]
    
    context = {
        "vacancy": vacancy,
        "response_form": response_form,
        "user_has_responded": user_has_responded,
        "responses": responses,
        "new_responses_count": new_responses_count,
        "similar_vacancies": similar_vacancies,
        "is_favorite": is_favorite,
    }
    return render(request, "vacancies/vacancy_detail.html", context)


@login_required
def send_vacancy_response(request, slug: str):
    """Отправка отклика на вакансию"""
    vacancy = get_object_or_404(
        Vacancy.objects.select_related("author"),
        slug=slug,
        is_active=True,
    )
    
    # Проверяем, что пользователь не является автором вакансии
    if request.user == vacancy.author:
        messages.error(request, "Вы не можете откликнуться на свою вакансию.")
        return redirect("vacancies:vacancy_detail", slug=vacancy.slug)
    
    # Проверяем, не откликался ли уже пользователь
    if VacancyResponse.objects.filter(vacancy=vacancy, applicant=request.user).exists():
        messages.error(request, "Вы уже откликались на эту вакансию.")
        return redirect("vacancies:vacancy_detail", slug=vacancy.slug)
    
    # Если GET запрос - показываем форму
    if request.method == "GET":
        form = VacancyResponseForm()
        return render(request, "vacancies/send_response.html", {
            "form": form,
            "vacancy": vacancy
        })
    
    # Если POST запрос - обрабатываем форму
    form = VacancyResponseForm(request.POST)
    if form.is_valid():
        response = form.save(commit=False)
        response.vacancy = vacancy
        response.applicant = request.user
        response.save()
        
        # Увеличиваем счетчик откликов
        vacancy.responses_count += 1
        vacancy.save(update_fields=['responses_count'])
        
        messages.success(request, "Ваш отклик успешно отправлен!")
        return redirect("vacancies:vacancy_detail", slug=vacancy.slug)
    
    messages.error(request, "Ошибка при отправке отклика.")
    return redirect("vacancies:vacancy_detail", slug=vacancy.slug)


@login_required
def my_vacancies(request):
    """Мои вакансии (для автора)"""
    vacancies = Vacancy.objects.filter(
        author=request.user
    ).select_related("specialty", "city", "city__region").order_by("-created_at")
    
    context = {
        "vacancies": vacancies,
    }
    return render(request, "vacancies/my_vacancies.html", context)


@login_required
def my_responses(request):
    """Мои отклики (для соискателя)"""
    responses = VacancyResponse.objects.filter(
        applicant=request.user
    ).select_related("vacancy", "vacancy__author", "vacancy__specialty", "vacancy__city", "vacancy__city__region").order_by("-created_at")
    
    context = {
        "responses": responses,
    }
    return render(request, "vacancies/my_responses.html", context)


@login_required
@require_POST
def mark_response_read(request, response_id):
    """Отметить отклик как прочитанный"""
    response = get_object_or_404(
        VacancyResponse.objects.select_related("vacancy", "vacancy__author"),
        pk=response_id,
        vacancy__author=request.user  # Только автор вакансии может отмечать отклики
    )
    
    if not response.is_read:
        response.is_read = True
        response.save(update_fields=['is_read'])
        messages.success(request, "Отклик отмечен как прочитанный")
    
    return redirect("vacancies:vacancy_detail", slug=response.vacancy.slug)


@login_required
def delete_vacancy(request, slug: str):
    """Удаление вакансии (архивирование)"""
    vacancy = get_object_or_404(
        Vacancy,
        slug=slug,
        author=request.user
    )
    
    if request.method == "POST":
        vacancy.is_active = False
        vacancy.save(update_fields=['is_active'])
        messages.success(request, "Вакансия успешно удалена")
        return redirect("vacancies:my_vacancies")
    
    context = {
        "vacancy": vacancy,
    }
    return render(request, "vacancies/delete_vacancy.html", context)


@login_required
@require_POST
def toggle_favorite_vacancy(request, slug: str):
    """Добавление/удаление вакансии в избранное"""
    vacancy = get_object_or_404(
        Vacancy,
        slug=slug,
        is_active=True,
        is_moderated=True
    )
    
    # Проверяем, не является ли пользователь автором вакансии
    if request.user == vacancy.author:
        messages.error(request, "Вы не можете добавить свою вакансию в избранное")
        return redirect("vacancies:vacancy_detail", slug=vacancy.slug)
    
    favorite, created = FavoriteVacancy.objects.get_or_create(
        user=request.user,
        vacancy=vacancy
    )
    
    if created:
        messages.success(request, "Вакансия добавлена в избранное")
    else:
        favorite.delete()
        messages.success(request, "Вакансия удалена из избранного")
    
    return redirect("vacancies:vacancy_detail", slug=vacancy.slug)


@login_required
def favorite_vacancies(request):
    """Список избранных вакансий"""
    favorites = FavoriteVacancy.objects.filter(
        user=request.user
    ).select_related("vacancy", "vacancy__specialty", "vacancy__author", "vacancy__city", "vacancy__city__region").order_by("-created_at")
    
    context = {
        "favorites": favorites,
    }
    return render(request, "vacancies/favorite_vacancies.html", context)


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
