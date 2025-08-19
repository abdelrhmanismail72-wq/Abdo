from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
import os
from dotenv import load_dotenv


# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-this-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jazzmin',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'core.log_ip_middleware.LogIPMiddleware',  # يمكن تفعيله لاحقاً إذا لزم الأمر
]

ROOT_URLCONF = 'edu_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ]},
    },
]

WSGI_APPLICATION = 'edu_platform.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4, # إعادة الطول إلى 4 بناءً على الطلب
        }
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/after_login/'
# at bottom of settings.py
import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# إعدادات الشبكة
if DEBUG:
    import socket
    
    # السماح بالوصول من أي عنوان IP
    ALLOWED_HOSTS = ['*']
    
    try:
        # الحصول على عنوان IP المحلي
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print("\n" + "="*60)
        print(f"📌 للوصول المحلي: http://{local_ip}:8000")
        print(f"🌍 للوصول من الأجهزة الأخرى على نفس الشبكة")
        print("="*60 + "\n")
            
    except Exception as e:
        print(f"\n⚠️ تحذير: {str(e)}")
        print("📌 الموقع يعمل على العنوان: http://localhost:8000\n")


# للتأكد من أن static و media يخدمهم runserver أثناء التطوير:
# (لا نضع هذا في production كما هو)

JAZZMIN_SETTINGS = {
    "site_title": "لوحة إدارة المنصة",
    "site_header": "إدارة المنصة",
    "site_brand": "منصة تعليمية",
    "welcome_sign": "مرحباً بك في لوحة الإدارة",
    "primary_color": "#25d366",  # لون رئيسي مثل واتساب
    "secondary_color": "#075e54",
    "show_sidebar": True,
    "navigation_expanded": True,
    "custom_css": "static/style.css",  # يمكنك ربط CSS خاص بك
    # ...إعدادات أخرى كثيرة...
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@example.com')

# Password Reset Settings
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours in seconds

# Frontend URL for password reset links (used in emails)
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8000')

