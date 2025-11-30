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
    path('profile/my-vacancies/', views.my_vacancies, name='my_vacancies'),
    path('user/<str:username>/', views.public_profile, name='public_profile'),
    # Жалобы и модерация
    path('complaint/', views.file_complaint, name='file_complaint'),
    path('complaint/<int:user_id>/', views.file_complaint, name='file_complaint_user'),
    path('moderation/', views.moderation_panel, name='moderation_panel'),
    path('moderation/complaint/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('moderation/warning/', views.issue_warning, name='issue_warning'),
    path('moderation/warning/<int:user_id>/', views.issue_warning, name='issue_warning_user'),
    path('moderation/ban/', views.issue_ban, name='issue_ban'),
    path('moderation/ban/<int:user_id>/', views.issue_ban, name='issue_ban_user'),
    # Уведомления
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<str:notification_type>/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]