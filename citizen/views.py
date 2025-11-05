from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, GrievanceSerializer
from .models import Grievance
from rest_framework.permissions import IsAuthenticated

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
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

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({"detail": "Use /api/token/ for login (POST username & password)"}, status=status.HTTP_400_BAD_REQUEST)

class GrievanceListCreateView(generics.ListCreateAPIView):
    serializer_class = GrievanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Grievance.objects.filter(citizen=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)
