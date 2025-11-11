from django.shortcuts import get_object_or_404, render

from .models import Article, Category


def get_categories():
    """Вспомогательная функция для получения категорий с количеством статей"""
    categories = Category.objects.all()
    for category in categories:
        category.articles_count = Article.objects.filter(
            category=category,
            public=True
        ).count()
    return categories


def get_popular_articles(limit=5):
    """Вспомогательная функция для получения популярных статей"""
    return Article.objects.filter(
        public=True,
        sidebar=True
    ).order_by('-create_at')[:limit]


def article_list(request):
    """Список статей"""
    articles = Article.objects.filter(public=True).order_by('-create_at')
    categories = get_categories()
    popular_articles = get_popular_articles()
    
    context = {
        'articles': articles,
        'categories': categories,
        'selected_category': None,
        'popular_articles': popular_articles,
    }
    return render(request, 'articles/article_list.html', context)


def articles_by_category(request, category_slug):
    """Статьи по категории"""
    category = get_object_or_404(Category, slug=category_slug)
    articles = Article.objects.filter(
        category=category,
        public=True
    ).order_by('-create_at')
    categories = get_categories()
    popular_articles = get_popular_articles()
    
    context = {
        'articles': articles,
        'categories': categories,
        'selected_category': category,
        'popular_articles': popular_articles,
    }
    return render(request, 'articles/article_list.html', context)


def article_detail(request, slug):
    """Детальная страница статьи"""
    article = get_object_or_404(
        Article.objects.filter(public=True),
        slug=slug
    )
    
    # Увеличиваем счетчик просмотров
    article.views += 1
    article.save(update_fields=['views'])
    
    categories = get_categories()
    popular_articles = get_popular_articles()
    
    context = {
        'article': article,
        'categories': categories,
        'selected_category': article.category if article.category else None,
        'popular_articles': popular_articles,
    }
    return render(request, 'articles/article_detail.html', context)
