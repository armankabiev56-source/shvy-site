from pathlib import Path
import os
import pymysql
# pymysql.install_as_MySQLdb()
# ====================== БАЗОВЫЕ НАСТРОЙКИ ======================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure'  
# ← Если хочешь оставить свой старый SECRET_KEY — просто замени эту строку на свою из старого файла

DEBUG = True

ALLOWED_HOSTS = ['*']   # для локальной разработки и потом для хостинга

# ====================== ПРИЛОЖЕНИЯ ======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',                    # наш основной app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shvy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'shvy.wsgi.application'

# ====================== БАЗА ДАННЫХ ======================
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'shvy_db',
#         'USER': 'shvy_user',
#         'PASSWORD': 'Arman_87081642549_@',
#         'HOST': 'localhost',
#         'PORT': '3306',
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         },
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
    }
}

# ====================== ПАРОЛИ И ЛОКАЛИЗАЦИЯ ======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Almaty'
USE_I18N = True
USE_TZ = True

# ====================== СТАТИКА И МЕДИА ======================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Для корректного отображения css в разработке
if DEBUG:
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)

# ====================== ДРУГОЕ ======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Для продакшена (Render)
if not DEBUG:
    ALLOWED_HOSTS = ['*']  # на время теста, потом замени на реальный домен
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True