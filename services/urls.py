from django.urls import path

from .views import (
    service_detail,
    service_list,
    create_service,
    edit_service,
    get_categories_by_section,
    get_cities_by_region,
    send_service_message,
    service_messages,
)

app_name = "services"

urlpatterns = [
    path("", service_list, name="service_list"),
    path("create/", create_service, name="create_service"),
    path("<slug:slug>/", service_detail, name="service_detail"),
    path("<slug:slug>/edit/", edit_service, name="edit_service"),
    path("<slug:slug>/messages/", service_messages, name="service_messages"),
    path("<slug:slug>/send-message/", send_service_message, name="send_service_message"),
    path("ajax/categories/", get_categories_by_section, name="get_categories_by_section"),
    path("ajax/cities/", get_cities_by_region, name="get_cities_by_region"),
]
