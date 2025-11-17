# officer/urls.py
from django.urls import path
from .views import OfficerDashboardView

app_name = 'officer'

urlpatterns = [
    path('dashboard/', OfficerDashboardView.as_view(), name='dashboard'),
]
