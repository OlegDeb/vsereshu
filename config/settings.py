import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-d1)=i8&afj=-c7ft06+ero$=egw=iy$g7ac7hm)=uznio#snt5'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'users', 
    'main',
    'categories',
    'regions',
    'tasks',
    'services',

    'crispy_forms',
    'crispy_bootstrap5',
]

AUTH_USER_MODEL = 'users.CustomUser'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vsedbreshu3570',
        'USER': 'vseusreshu2903',
        'PASSWORD': 'Hdwsoiwe8923jfdi2348',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # папка со статикой в корне проекта
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # для collectstatic

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_REDIRECT_URL = 'profile'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
