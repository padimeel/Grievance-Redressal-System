
# # from rest_framework import generics, permissions
# # from .models import Grievance, Feedback
# # #from .serializers import GrievanceSerializer, FeedbackSerializer
# # from .serializers import RegisterSerializer, GrievanceSerializer, FeedbackSerializer


# # class GrievanceListCreateView(generics.ListCreateAPIView):
# #     serializer_class = GrievanceSerializer
# #     permission_classes = [permissions.IsAuthenticated]

# #     def get_queryset(self):
# #         return Grievance.objects.filter(citizen=self.request.user).order_by('-created_at')

# #     def perform_create(self, serializer):
# #         serializer.save(citizen=self.request.user)


# # class FeedbackCreateView(generics.CreateAPIView):
# #     serializer_class = FeedbackSerializer
# #     permission_classes = [permissions.IsAuthenticated]

# from rest_framework import generics, permissions
# from .models import Grievance, Feedback
# from .serializers import RegisterSerializer, GrievanceSerializer, FeedbackSerializer


# class GrievanceListCreateView(generics.ListCreateAPIView):
#     """
#     GET: List all grievances for the logged-in citizen.
#     POST: Create a new grievance for the logged-in citizen.
#     """
#     serializer_class = GrievanceSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return Grievance.objects.filter(citizen=self.request.user).order_by('-created_at')

#     def perform_create(self, serializer):
#         serializer.save(citizen=self.request.user)


# class FeedbackCreateView(generics.CreateAPIView):
#     """
#     POST: Submit feedback for the system (logged-in users only).
#     """
#     queryset = Feedback.objects.all()
#     serializer_class = FeedbackSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         serializer.save(citizen=self.request.user)  # only if your Feedback model has this field


from rest_framework import serializers
from .models import Grievance, Feedback
from django.contrib.auth.models import User 
# or your custom User model


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from .serializers import GrievanceSerializer, FeedbackSerializer, RegisterSerializer
from .models import Grievance


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
                "refresh": str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "id": user.id,
                "username": user.username,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)



class GrievanceListCreateView(generics.ListCreateAPIView):
    serializer_class = GrievanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Grievance.objects.filter(citizen=self.request.user)

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)




    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class GrievanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grievance
        fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
