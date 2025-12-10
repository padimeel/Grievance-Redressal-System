# citizen/urls.py
from django.urls import path
from .views import CitizenDashboardView, GrievanceListView, GrievanceCreateView, GrievanceDetailView

app_name = 'citizen'

urlpatterns = [
    path('dashboard/', CitizenDashboardView.as_view(), name='dashboard'),
    path('grievances/', GrievanceListView.as_view(), name='grievance-list'),
    path('grievances/new/', GrievanceCreateView.as_view(), name='grievance-create'),
    path('grievances/<int:pk>/', GrievanceDetailView.as_view(), name='grievance-detail')  # new

]

