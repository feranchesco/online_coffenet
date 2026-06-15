# home_module/urls.py

from django.urls import path
from . import views, chat_views

urlpatterns = [
    # صفحه اصلی
    path('', views.home, name='home'),
    # API خدمات صفحه اصلی
    path('api/home-services/', views.get_home_services_api, name='home_services_api'),

    # API ایجاد سرویس جدید
    path('api/service/create/', views.create_service, name='create_service'),
    # چت (بدون @login_required - احراز هویت در خود view انجام میشه)
    path('api/chat/<uuid:service_id>/messages/', chat_views.get_messages, name='get_messages'),
    path('api/chat/<uuid:service_id>/send/', chat_views.send_message, name='send_message'),
    path('api/chat/<uuid:service_id>/read/', chat_views.mark_as_read, name='mark_as_read'),
    path('api/chat/unread/', chat_views.get_unread_count, name='get_unread_count'),
    path('api/chat/list/', chat_views.get_chat_list, name='get_chat_list'),
    # API ها
    path('api/service/create/', views.create_service, name='create_service'),
    path('api/service/<uuid:service_id>/pay/', views.pay_service, name='pay_service'),
    path('api/service/<uuid:service_id>/download/', views.download_result, name='download_result'),
    path('api/service/<uuid:service_id>/rate/', views.rate_service, name='rate_service'),
    path('api/news/', views.news_list_api, name='news_list_api'),
    path('ai-chat/', views.ai_chat_page, name='ai_chat_page'),
    path('api/ai-chat/send/', views.ai_chat_api, name='ai_chat_api'),
    path('api/ai-chat/history/<uuid:session_id>/', views.get_chat_history, name='ai_chat_history'),

]