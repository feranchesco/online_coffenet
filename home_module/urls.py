from django.urls import path

from home_module import views

from . import chat_views
urlpatterns = [
    path('', views.home, name='home'),
    path('api/chat/<uuid:service_id>/messages/', chat_views.get_messages, name='get_messages'),
    path('api/chat/<uuid:service_id>/send/', chat_views.send_message, name='send_message'),
    path('api/chat/<uuid:service_id>/read/', chat_views.mark_as_read, name='mark_as_read'),
    path('api/chat/unread/', chat_views.get_unread_count, name='get_unread_count'),
    path('api/chat/list/', chat_views.get_chat_list, name='get_chat_list'),
]