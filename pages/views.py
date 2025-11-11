from django.shortcuts import get_object_or_404, render

from .models import Page


def get_pages_list():
    """Вспомогательная функция для получения списка активных страниц"""
    return Page.objects.filter(is_active=True).order_by('title')


def page_list(request):
    """Список всех статических страниц"""
    pages = get_pages_list()
    
    context = {
        "pages": pages,
        "pages_list": pages,  # Для сайдбара
    }
    return render(request, "pages/page_list.html", context)


def page_detail(request, slug):
    """Отображение статической страницы"""
    page = get_object_or_404(
        Page.objects.filter(is_active=True),
        slug=slug
    )
    
    # Получаем все активные страницы для сайдбара
    pages_list = get_pages_list()
    
    context = {
        "page": page,
        "pages_list": pages_list,
    }
    return render(request, "pages/page_detail.html", context)
