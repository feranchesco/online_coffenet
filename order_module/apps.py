# order_module/apps.py

from django.apps import AppConfig


class OrderModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order_module'
    verbose_name = 'ماژول سفارشات و پرداخت'

    def ready(self):
        # ثبت admin ها
        import order_module.admin