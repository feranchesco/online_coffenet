from django.urls import path
from account_module import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('signup/', views.signup, name='signup'),
    path('admin/', admin.site.urls),
    # احراز هویت
    path('cu-login/', views.CustomerLogin.as_view(), name='customer_login'),
    path('cu-signup/', views.CustomerSignup.as_view(), name='customer_signup'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('profile/', views.profile, name='profile'),  # ✅ جدید
    # اپراتور
    path('op-panel/', views.operator_panel, name='operator_panel'),
    path('op-signup', views.OperatorSignup.as_view(), name='operator_signup'),
    path('op-login', views.OperatorLogin.as_view(), name='operator_login'),
    path('op-logout', views.operator_logout, name='operator_logout'),
]

# سرو فایل‌های static و media در حالت development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
