# проект/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('main.urls')),
    path('services/', include('services.urls')),
    path('tasks/', include('tasks.urls')),
    path('vacancies/', include('vacancies.urls')),
    path('articles/', include('articles.urls')),
    path('categories/', include('categories.urls')),
    path('locations/', include('regions.urls')),
    path('info/', include('pages.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)