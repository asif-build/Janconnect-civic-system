from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),   # Default page
    path('login/', views.login_view, name='login'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path("heatmap-data/", views.heatmap_data, name="heatmap_data"),

    path('add/', views.add_page, name='add_page'),
    path('api/add/', views.add_complaint_api, name='add_complaint_api'),

    # 🔹 Complaint status actions
    path('resolve/<int:id>/', views.resolve_complaint, name='resolve_complaint'),
    path('confirm/<int:id>/', views.confirm_resolution, name='confirm_resolution'),
    path('register/', views.register_view, name='register'),

]