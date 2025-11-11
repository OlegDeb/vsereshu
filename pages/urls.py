from django.urls import path

from .views import page_list, page_detail

app_name = "pages"

urlpatterns = [
    path("", page_list, name="page_list"),
    path("<slug:slug>/", page_detail, name="page_detail"),
]

