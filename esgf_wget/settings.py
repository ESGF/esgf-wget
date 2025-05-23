"""
Django settings for esgf_wget project.

Generated by 'django-admin startproject' using Django 2.2.12.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import configparser

SECRET_KEY = os.getenv('ESGF_WGET_SECRET_KEY', default=None)

if SECRET_KEY is None:
    raise Exception('ESGF_WGET_SECRET_KEY is not set.')

config = configparser.RawConfigParser()

config_file = os.getenv('ESGF_WGET_CONFIG', default=None)

if config_file is None or not os.path.isfile(config_file):
    raise Exception('ESGF_WGET_CONFIG is not set, or is not a file.')

try:
    config.read(config_file)
except IOError:
    raise Exception('Unable to load config file.')

DEBUG = config['django'].getboolean('DEBUG', True)
ALLOWED_HOSTS = config['django'].get('ALLOWED_HOSTS', '').split(',')
DATA_UPLOAD_MAX_NUMBER_FIELDS = config['django'].getint(
    'DATA_UPLOAD_MAX_NUMBER_FIELDS', 10240)

GLOBUS_UUID = config['wget'].get("GLOBUS_UUID", "")

ESGF_ALLOWED_PROJECTS_JSON = config['wget'].get(
    'ESGF_ALLOWED_PROJECTS_JSON', '')
WGET_SCRIPT_FILE_DEFAULT_LIMIT = config['wget'].getint(
    'WGET_SCRIPT_FILE_DEFAULT_LIMIT', 1000)
WGET_SCRIPT_FILE_MAX_LIMIT = config['wget'].getint(
    'WGET_SCRIPT_FILE_MAX_LIMIT', 100000)
WGET_MAX_DIR_LENGTH = config['wget'].getint(
    'WGET_MAX_DIR_LENGTH', 50)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

# Application definition

INSTALLED_APPS = [
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'esgf_wget.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_PATH, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'esgf_wget.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
