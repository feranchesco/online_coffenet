from django.urls import path
from account_module import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('admin/', admin.site.urls),
    # احراز هویت
    path('login/', views.customer_login, name='customer_login'),
    path('register/', views.customer_register, name='customer_register'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('profile/', views.profile, name='profile'),  # ✅ جدید

    # پنل مشتری
    # path('panel/', views.customer_panel, name='customer_panel'),

    # API ها
    path('api/service/create/', views.create_service, name='create_service'),
    path('api/service/<uuid:service_id>/pay/', views.pay_service, name='pay_service'),
    path('api/service/<uuid:service_id>/download/', views.download_result, name='download_result'),
    path('api/service/<uuid:service_id>/rate/', views.rate_service, name='rate_service'),
]

# سرو فایل‌های static و media در حالت development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)