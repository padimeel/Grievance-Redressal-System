# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import login_page, register_page
from .views import get_user_role


# Root page
def index(request):
    content = """
    <h2>Grievance Redressal API</h2>
    <p>Available endpoints:</p>
    <ul>
      <li><a href='/admin/'>/admin/</a></li>
      <li>/api/v1/citizen/register/ (POST)</li>
      <li>/api/v1/citizen/grievances/ (GET/POST, JWT auth)</li>
      <li>/api/token/ (POST username/password)</li>
    </ul>
    """
    return HttpResponse(content, content_type="text/html")

# Login page view
def login_page(request):
    return render(request, 'citizen/login.html')


urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('api/v1/citizen/', include('citizen.urls')),
    path('api/v1/officer/', include('officer.urls')),
    path('api/v1/adminpanel/', include('adminpanel.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user-role/', get_user_role, name='user-role')
]








