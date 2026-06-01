from django.urls import path

from account_module import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
]