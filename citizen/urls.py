# citizen/urls.py
from django.urls import path

from .views import RegisterView, GrievanceListCreateView



urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    # OR if using auto-login:
    # path('auth/register/', RegisterAndLoginView.as_view(), name='register_and_login'),

    path('citizens/grievances/', GrievanceListCreateView.as_view(), name='grievance-list-create'),
    #path('citizens/feedback/', FeedbackCreateView.as_view(), name='feedback-create'),
    

]

from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('grievances/', views.GrievanceListCreateView.as_view(), name='grievance-list-create'),
]

