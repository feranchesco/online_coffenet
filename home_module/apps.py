# home_module/apps.py

from django.apps import AppConfig


class HomeModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home_module'
    verbose_name = 'ماژول اصلی (خدمات و چت)'