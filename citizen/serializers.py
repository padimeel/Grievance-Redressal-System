# # citizen/serializers.py (append at end)

# from django.contrib.auth.models import User
# from rest_framework.validators import UniqueValidator
# from rest_framework import serializers

# from .models import Category, Grievance, Feedback
# from django.contrib.auth.models import User
# from rest_framework.validators import UniqueValidator

# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ['id', 'name']


# class GrievanceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Grievance
#         fields = '__all__'

# class RegisterSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(
#         required=False,
#         validators=[UniqueValidator(queryset=User.objects.all())]
#     )
#     password = serializers.CharField(write_only=True, min_length=8)

#     class Meta:
#         model = User
#         fields = ("id", "username", "email", "password", "first_name", "last_name")
#         read_only_fields = ("id",)

#     def create(self, validated_data):

#         category_data = validated_data.pop('category', None)
#         if category_data:
#             category, _ = Category.objects.get_or_create(name=category_data['name'])
#             validated_data['category'] = category

#         user = self.context['request'].user
#         grievance = Grievance.objects.create(citizen=user, **validated_data)
#         return grievance


# class FeedbackSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Feedback
#         fields = ['id', 'grievance', 'rating', 'comments', 'created_at']


# class RegisterSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(
#         required=False,
#         validators=[UniqueValidator(queryset=User.objects.all())]
#     )
#     password = serializers.CharField(write_only=True, min_length=8)

#     class Meta:
#         model = User
#         fields = ("id", "username", "email", "password", "first_name", "last_name")
#         read_only_fields = ("id",)

#     def create(self, validated_data):

#         password = validated_data.pop("password")
#         user = User(**validated_data)
#         user.set_password(password)
#         user.save()

from rest_framework import serializers
from .models import Grievance, Feedback, User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

class GrievanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grievance
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'

