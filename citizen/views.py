# citizen/views.py
from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404

from .models import Grievance
from .serializers import GrievanceSerializer, FeedbackSerializer, RegisterSerializer


class RegisterView(APIView):
    """
    Register a new user and return JWT tokens (access + refresh).
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "id": user.id,
                "username": user.username,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Use the built-in Simple JWT view for login
LoginView = TokenObtainPairView


class GrievanceListCreateView(generics.ListCreateAPIView):
    """
    GET: list grievances for the requesting (authenticated) citizen.
    POST: create a new grievance associated to the authenticated user.
    """
    serializer_class = GrievanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return grievances only for the current user
        return Grievance.objects.filter(citizen=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # When creating, save the citizen as the request.user.
        serializer.save(citizen=self.request.user)
