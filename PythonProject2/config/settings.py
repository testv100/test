from pathlib import Path

# БАЗОВЫЕ НАСТРОЙКИ ПУТЕЙ
BASE_DIR = Path(__file__).resolve().parent.parent

# ОБЯЗАТЕЛЬНО: секретный ключ (для разработки можно любой)
SECRET_KEY = 'django-insecure-edu-analytics-demo-secret-key-1234567890'

# РЕЖИМ ОТЛАДКИ (для разработки должен быть True)
DEBUG = True

ALLOWED_HOSTS = []


# ПРИЛОЖЕНИЯ
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'analytics',  # наше приложение
]


# ПРОМЕЖУТОЧНОЕ ПО (middleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# КОРНЕВОЙ ФАЙЛ URL
ROOT_URLCONF = 'config.urls'


# ШАБЛОНЫ
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Можно и без DIRS, т.к. у нас шаблоны внутри приложения,
        # но на всякий случай добавим:
        'DIRS': [BASE_DIR / 'analytics' / 'templates'],
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


# WSGI-ПРИЛОЖЕНИЕ
WSGI_APPLICATION = 'config.wsgi.application'


# БАЗА ДАННЫХ (SQLite для локальной разработки)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ВАЛИДАТОРЫ ПАРОЛЕЙ (можно оставить как есть)
AUTH_PASSWORD_VALIDATORS = []


# ЛОКАЛИЗАЦИЯ
LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Vilnius'  # можешь поставить 'Europe/Moscow', если хочешь

USE_I18N = True
USE_TZ = True


# СТАТИЧЕСКИЕ ФАЙЛЫ
STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


# АВТОТИП ПОЛЕЙ ID
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/admin/login/'
