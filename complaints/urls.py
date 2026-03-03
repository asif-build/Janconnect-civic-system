from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),   # Default page
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_page, name='add_page'),
    path('api/add/', views.add_complaint_api, name='add_complaint_api'),
]