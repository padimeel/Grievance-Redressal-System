# backend/citizen/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Grievance,Feedback
from rest_framework import serializers

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')

class GrievanceSerializer(serializers.ModelSerializer):
    # Accept category (id) or category_name (string)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    category_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Grievance
        fields = (
            'id', 'user', 'category', 'category_name',
            'title', 'description', 'attachment',
            'status', 'assigned_to', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'status', 'created_at', 'updated_at')

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        category_name = validated_data.pop('category_name', None)
        category = validated_data.pop('category', None)

        if category is None and category_name:
            category, _ = Category.objects.get_or_create(name=category_name.strip())

        grievance = Grievance.objects.create(user=user, category=category, **validated_data)
        return grievance

class GrievanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grievance
        fields = ('status', 'assigned_to')

class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Feedback
        fields = ('id', 'grievance', 'user', 'rating', 'comments', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)
