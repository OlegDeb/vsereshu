from django.urls import path

from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('category/<slug:category_slug>/', views.articles_by_category, name='articles_by_category'),
    path('<slug:slug>/', views.article_detail, name='article_detail'),
]
