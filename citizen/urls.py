# citizen/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),            # JWT login endpoint
    path('grievances/', views.GrievanceListCreateView.as_view(), name='grievance-list-create'),
]


