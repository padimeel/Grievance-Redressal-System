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
from django.contrib.auth.models import User  # or your custom User model


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

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
