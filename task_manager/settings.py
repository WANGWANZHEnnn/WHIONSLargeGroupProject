"""
Django settings for task_manager project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from django.contrib.messages import constants as messages
import os
import dj_database_url
import celery
from celery import Celery
from datetime import datetime, time, timedelta


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-&$dln5wpgorppuw&(gintxm573v2ks+zq4o$(4*lapguixf^+2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'tasks',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'celery',
    'django_celery_beat',
    'ckeditor',
    'ckeditor_uploader',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'task_manager.urls'

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
            'tasks.context_processor.add_journal_streak',
            ],
            },
            },
]

WSGI_APPLICATION = 'task_manager.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases



IS_HEROKU_APP = "DYNO" in os.environ and not "CI" in os.environ

DATABASES = {
'default': {
'ENGINE': 'django.db.backends.sqlite3',
'NAME': BASE_DIR / 'db.sqlite3',
}
}


if IS_HEROKU_APP:
    db_from_env = dj_database_url.config(conn_max_age=600)
    DATABASES = {
        'default': db_from_env
    }






# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/images/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'static/images')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# User model for authentication and login purposes
AUTH_USER_MODEL = 'tasks.User'

# Login URL for redirecting users from login protected views
LOGIN_URL = 'log_in'

# URL where @login_prohibited redirects to
REDIRECT_URL_WHEN_LOGGED_IN = 'dashboard'

# Convert Django ERROR messages to Bootstrap DANGER messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# SMTP server settings
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587  
EMAIL_USE_TLS = True 

# Email account credentials
EMAIL_HOST_USER = 'WHIONS@outlook.com'
EMAIL_HOST_PASSWORD = 'ozsaerdncmitzndb'
EMAIL_FROM = 'WHIONS@outlook.com'
DEFAULT_FROM_EMAIL = 'WHIONS@outlook.com'


# Celery settings
from celery.schedules import crontab
CELERY_TIMEZONE = "Europe/London"

REDIS_URL = os.environ.get('REDIS_URL')

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_IMPORTS = ("tasks", )
CELERY_BEAT_SCHEDULE = {
    'trigger_reminder_emails_daily': {
        'task': 'tasks.tasks.check_and_trigger_reminder_emails',
        'schedule': crontab(minute=0, hour=0),# Run daily at midnight
    },
    'reset_flower_growth_if_no_entry': {
        'task': 'tasks.tasks.reset_flower_growth_if_no_entry',
        'schedule': crontab(minute=0, hour=0),# Run daily at midnight
    },
    'reset_flower_growth_weekly': {
        'task': 'tasks.tasks.reset_flower_growth_weekly',
        'schedule': crontab(minute=0, hour=0, day_of_week='sun'),# Run at the start of each week
    },

}


CKEDITOR_BASE_PATH = "/static/ckeditor/ckeditor/"
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_IMAGE_BACKEND = "pillow"

WHITENOISE_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# This is to configure what the user can use with the ckeditor
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
    { 'name': 'styles', 'items': ['Format', 'Font', 'FontSize'] },
    { 'name': 'basicstyles', 'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript'] },
    { 'name': 'paragraph', 'items': ['NumberedList', 'BulletedList', 'Outdent', 'Indent', 'JustifyLeft', 'JustifyCenter', 'JustifyRight'] },
    { 'name': 'links', 'items': ['Link', 'Unlink'] },
    { 'name': 'insert', 'items': ['Image'] },
    { 'name': 'tools', 'items': ['Maximize'] }
]
    }
    }