"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
<<<<<<< HEAD
# backend/backend/urls.py
=======

>>>>>>> cdefe324fb784ba2e59e8154ab172cdbfb69ecc7
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
<<<<<<< HEAD
    path('api/v1/', include('citizen.urls')),   # your app APIs
=======

    # App-level routes
    path('api/v1/citizen/', include('citizen.urls')),       # all citizen-related APIs
    path('api/v1/officer/', include('officer.urls')),       # officer module (if any)
    path('api/v1/adminpanel/', include('adminpanel.urls')), # adminpanel module

    # JWT Authentication endpoints
>>>>>>> cdefe324fb784ba2e59e8154ab172cdbfb69ecc7
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
