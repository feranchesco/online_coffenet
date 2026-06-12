# admin_panel/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # صفحه اصلی پنل مدیریت
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),

    # API ها
    path('api/admin/projects/', views.api_get_projects, name='api_get_projects'),
    path('api/admin/projects/<uuid:project_id>/', views.api_get_project_detail, name='api_get_project_detail'),
    path('api/admin/projects/<uuid:project_id>/delete/', views.api_delete_project, name='api_delete_project'),
    path('api/admin/projects/<uuid:project_id>/status/', views.api_update_project_status,
         name='api_update_project_status'),
    path('api/admin/projects/<uuid:project_id>/assign/', views.api_assign_operator, name='api_assign_operator'),
    path('api/admin/projects/<uuid:project_id>/update/', views.api_update_project, name='api_update_project'),

    path('api/admin/operators/', views.api_get_operators, name='api_get_operators'),
    path('api/admin/operators/list/', views.api_get_operators_list, name='api_get_operators_list'),
    path('api/admin/operators/<uuid:operator_id>/pay/', views.api_pay_operator, name='api_pay_operator'),

    path('api/admin/revenue/', views.api_get_revenue, name='api_get_revenue'),
    path('api/admin/news/', views.admin_news_list_api, name='admin_news_list'),
    path('api/admin/news/create/', views.admin_news_create_api, name='admin_news_create'),
    path('api/admin/news/<uuid:news_id>/update/', views.admin_news_update_api, name='admin_news_update'),
    path('api/admin/news/<uuid:news_id>/delete/', views.admin_news_delete_api, name='admin_news_delete'),

    # API مدیریت خدمات صفحه اصلی
    path('api/admin/home-services/', views.admin_home_services_list_api, name='admin_home_services_list'),
    path('api/admin/home-services/create/', views.admin_home_service_create_api, name='admin_home_service_create'),
    path('api/admin/home-services/<uuid:service_id>/update/', views.admin_home_service_update_api,
         name='admin_home_service_update'),
    path('api/admin/home-services/<uuid:service_id>/delete/', views.admin_home_service_delete_api,
         name='admin_home_service_delete'),
]