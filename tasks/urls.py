from django.urls import path

from .views import task_detail, task_list

app_name = "tasks"

urlpatterns = [
    path("", task_list, name="task_list"),
    path("<slug:slug>/", task_detail, name="task_detail"),
]
