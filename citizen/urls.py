# citizen/urls.py
from django.urls import path
from .views import RegisterView, RegisterAndLoginView, GrievanceListCreateView, FeedbackCreateView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    # OR if using auto-login:
    # path('auth/register/', RegisterAndLoginView.as_view(), name='register_and_login'),

    path('citizens/grievances/', GrievanceListCreateView.as_view(), name='grievance-list-create'),
    path('citizens/feedback/', FeedbackCreateView.as_view(), name='feedback-create'),
]