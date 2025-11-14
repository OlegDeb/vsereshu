# users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "users"

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/my-tasks/', views.my_tasks, name='my_tasks'),
    path('profile/my-services/', views.my_services, name='my_services'),
    path('user/<str:username>/', views.public_profile, name='public_profile'),
]