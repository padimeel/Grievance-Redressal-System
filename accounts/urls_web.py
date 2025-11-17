# accounts/urls_api.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminUserViewSet, RegisterAPIView, MeAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    # JWT token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # public API register + profile ('me')
    path('register/', RegisterAPIView.as_view(), name='api-register'),
    path('me/', MeAPIView.as_view(), name='me'),

    # router urls (users management)
    path('', include(router.urls)),
]








