from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Главная страница услуг
    #path('', views.service_list, name='service_list'),
    
    # Услуги по категории
    #path('category/<str:category_slug>/', views.services_by_category, name='services_by_category'),
    
    # Услуги по городу
    #path('location/<str:region_slug>/<str:city_slug>/', views.services_by_city, name='services_by_city'),
    
    # Услуги категории в городе
    #path('location/<str:region_slug>/<str:city_slug>/category/<str:category_slug>/', views.services_by_city_category, name='services_by_city_category'),
    
    # Детальная страница услуги
    #path('service/<str:service_slug>/', views.service_detail, name='service_detail'),
    
    # Альтернатива: услуга с привязкой к городу и категории
    #path('location/<str:region_slug>/<str:city_slug>/category/<str:category_slug>/service/<str:service_slug>/', views.service_detail_full, name='service_detail_full'),
]