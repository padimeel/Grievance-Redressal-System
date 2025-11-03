from rest_framework import generics, permissions
from .models import Grievance, Feedback
from .serializers import GrievanceSerializer, FeedbackSerializer

class GrievanceListCreateView(generics.ListCreateAPIView):
    serializer_class = GrievanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Grievance.objects.filter(citizen=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)


class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

