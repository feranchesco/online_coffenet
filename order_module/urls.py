# order_module/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # صفحه پرداخت
    path('pay/<uuid:service_id>/', views.payment_page, name='payment_page'),

    # ارسال به درگاه
    path('pay/send/<uuid:service_id>/', views.send_to_gateway, name='send_to_gateway'),

    # وریفای پرداخت (بازگشت از درگاه)
    path('pay/confirm/', views.verify_payment, name='verify_payment'),

    # وریفای از سایت واسط
    path('pay/verify-from-other/', views.verify_from_other_site, name='verify_from_other'),

    # اعمال کد تخفیف
    path('pay/discount/<uuid:service_id>/', views.apply_discount_view, name='apply_discount'),

    # پرداخت از کیف پول
    path('pay/wallet/<uuid:service_id>/', views.pay_from_wallet, name='pay_from_wallet'),
]