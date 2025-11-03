from django.urls import path
from .views import GrievanceListCreateView, FeedbackCreateView

urlpatterns = [
    path('citizens/grievances/', GrievanceListCreateView.as_view(), name='grievance-list-create'),
    path('citizens/feedback/', FeedbackCreateView.as_view(), name='feedback-create'),
]
