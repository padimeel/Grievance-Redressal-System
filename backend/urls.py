from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Citizen APIs
    path('api/v1/citizen/', include('citizen.urls')),

    # Minimal includes for officer/adminpanel (each app should have its own urls.py)
    path('api/v1/officer/', include('officer.urls')),
    path('api/v1/adminpanel/', include('adminpanel.urls')),

    # JWT tokens
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
