from django.shortcuts import render
from categories.models import CategorySection, Category
from services.models import Service

# Create your views here.
def home(request):
    # Получаем все активные разделы категорий с их активными категориями
    sections = CategorySection.objects.filter(
        is_active=True
    ).prefetch_related(
        'categories'
    ).order_by('name')
    
    # Для каждого раздела получаем его активные категории
    sections_with_categories = []
    for section in sections:
        categories = section.categories.filter(is_active=True).order_by('name')
        if categories.exists():  # Показываем только разделы с категориями
            sections_with_categories.append({
                'section': section,
                'categories': categories
            })
    
    # Получаем последние услуги (только проверенные модератором и активные)
    latest_services = Service.objects.select_related(
        'category', 'city', 'author', 'category__section'
    ).filter(
        is_active=True,
        is_moderated=True
    ).order_by('-created_at')[:6]
    
    context = {
        'sections_with_categories': sections_with_categories,
        'latest_services': latest_services
    }
    return render(request, 'main/home.html', context)