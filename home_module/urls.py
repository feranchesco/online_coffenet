# home_module/urls.py

from django.urls import path
from . import views, chat_views

urlpatterns = [
    # صفحه اصلی
    path('', views.home, name='home'),
    path('oplogin/', views.operator_login, name='operator_login'),
    path('oppanel/', views.operator_panel, name='operator_panel'),
    # API خدمات صفحه اصلی
    path('api/home-services/', views.get_home_services_api, name='home_services_api'),

    # API ایجاد سرویس جدید
    path('api/service/create/', views.create_service, name='create_service'),

    # چت
    path('api/chat/<uuid:service_id>/messages/', chat_views.get_messages, name='get_messages'),
    path('api/chat/<uuid:service_id>/send/', chat_views.send_message, name='send_message'),
    path('api/chat/<uuid:service_id>/read/', chat_views.mark_as_read, name='mark_as_read'),
    path('api/chat/unread/', chat_views.get_unread_count, name='get_unread_count'),
    path('api/chat/list/', chat_views.get_chat_list, name='get_chat_list'),

]