# adminpanel/urls.py
from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    # Template views
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('grievances/', views.grievances_list_view, name='grievances_list'),
    path('grievances/<int:pk>/', views.grievance_detail_view, name='grievance_detail'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('users/', views.users_view, name='users'),
    path('categories/', views.categories_view, name='categories'),
    path('settings/', views.settings_page, name='settings'),
    path('users/add/', views.add_user_view, name='add_user'),
    path('users/<int:pk>/edit/', views.edit_user_view, name='edit_user'),

    # Password reset (template-based)
    path('reset-password/', views.reset_password_page, name='reset_password_page'),

    # API endpoints
    path('api/categories/', views.api_categories_list_create, name='api_categories'),
    path('api/categories/<int:pk>/', views.api_category_detail, name='api_category_detail'),

    path('api/users/', views.api_users_list_create, name='api_users_list'),
    path('api/users/<int:pk>/', views.api_user_detail, name='api_user_detail'),
    path('api/users/<int:pk>/reset_password/', views.api_user_send_reset, name='api_user_reset'),

    path('api/password_reset_confirm/', views.api_password_reset_confirm, name='api_password_reset_confirm'),

    path('api/grievances/', views.api_grievances_list, name='api_grievances_list'),
    path('api/grievances/<int:pk>/', views.api_grievance_detail, name='api_grievance_detail'),
    path('api/grievances/<int:pk>/assign/', views.api_grievance_assign, name='api_grievance_assign'),
    path('api/grievances/<int:pk>/remarks/', views.api_grievance_add_remark, name='api_grievance_add_remark'),
    path('api/export/grievances/', views.api_export_grievances_csv, name='api_export_grievances'),

    path('api/analytics/', views.api_analytics, name='api_analytics'),
    path('api/user-status/', views.api_user_status, name='api_user_status'),

    # Dev-only debug endpoint (remove in production)
    path('debug/inspect/', views.debug_request_inspect, name='debug_inspect'),
]



