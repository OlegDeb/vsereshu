from django.shortcuts import render
from categories.models import CategorySection, Category

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
    
    context = {
        'sections_with_categories': sections_with_categories
    }
    return render(request, 'main/home.html', context)