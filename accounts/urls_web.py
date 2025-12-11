# accounts/urls_api.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterAPI,
    MeAPI,
    AdminUserListCreateAPI,
    AdminUserDetailAPI,
)

urlpatterns = [
    # JWT token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # public API register + profile ('me')
    path('register/', RegisterAPI.as_view(), name='api-register'),
    path('me/', MeAPI.as_view(), name='me'),

    # Admin user management (plain APIViews — NOT using router)
    path('admin/users/', AdminUserListCreateAPI.as_view(), name='admin-users-list-create'),
    path('admin/users/<int:pk>/', AdminUserDetailAPI.as_view(), name='admin-users-detail'),
]








