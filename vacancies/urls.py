from django.urls import path
from . import views

app_name = "vacancies"

urlpatterns = [
    # Главная страница вакансий
    path("", views.vacancy_list, name="vacancy_list"),
    
    # Создание и редактирование вакансий
    path("create/", views.create_vacancy, name="create_vacancy"),
    path("edit/<slug:slug>/", views.edit_vacancy, name="edit_vacancy"),
    
    # Личные страницы (должны быть ВЫШЕ паттерна со слагом)
    path("my-vacancies/", views.my_vacancies, name="my_vacancies"),
    path("my-responses/", views.my_responses, name="my_responses"),
    
    # Избранные вакансии (должны быть ВЫШЕ паттерна со слагом)
    path("favorites/", views.favorite_vacancies, name="favorite_vacancies"),
    
    # Отклики на вакансии
    path("respond/<slug:slug>/", views.send_vacancy_response, name="send_vacancy_response"),
    
    # Детальная страница вакансии (должна быть ПОСЛЕ конкретных путей)
    path("<slug:slug>/", views.vacancy_detail, name="vacancy_detail"),
    
    # Управление откликами и вакансиями
    path("response/<int:response_id>/mark-read/", views.mark_response_read, name="mark_response_read"),
    path("delete/<slug:slug>/", views.delete_vacancy, name="delete_vacancy"),
    
    # Избранные вакансии (добавление/удаление)
    path("favorite/<slug:slug>/", views.toggle_favorite_vacancy, name="toggle_favorite_vacancy"),
    
    # AJAX для загрузки городов
    path("ajax/cities/", views.get_cities_by_region, name="get_cities_by_region"),
]