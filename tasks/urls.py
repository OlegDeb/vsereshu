from django.urls import path

from .views import (
    task_detail,
    task_list,
    create_task,
    edit_task,
    create_response,
    response_detail,
    send_message,
    update_response_status,
    complete_task,
    accept_task_completion,
    create_review,
    get_categories_by_section,
    get_cities_by_region,
)

app_name = "tasks"

urlpatterns = [
    path("", task_list, name="task_list"),
    path("create/", create_task, name="create_task"),
    path("<slug:slug>/", task_detail, name="task_detail"),
    path("<slug:slug>/edit/", edit_task, name="edit_task"),
    path("<slug:slug>/respond/", create_response, name="create_response"),
    path("<slug:slug>/complete/", complete_task, name="complete_task"),
    path("<slug:slug>/accept/", accept_task_completion, name="accept_task_completion"),
    path("<slug:slug>/review/<int:user_id>/", create_review, name="create_review"),
    path("responses/<int:response_id>/", response_detail, name="response_detail"),
    path("responses/<int:response_id>/send-message/", send_message, name="send_message"),
    path("responses/<int:response_id>/update-status/", update_response_status, name="update_response_status"),
    path("ajax/categories/", get_categories_by_section, name="get_categories_by_section"),
    path("ajax/cities/", get_cities_by_region, name="get_cities_by_region"),
]
