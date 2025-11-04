from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from .models import Category, Grievance, Feedback

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']

class GrievanceSerializer(serializers.ModelSerializer):
    # Accept either nested category object or category id
    category = CategorySerializer(required=False, allow_null=True)

    class Meta:
        model = Grievance
        fields = ['id', 'citizen', 'category', 'title', 'description', 'status', 'created_at']
        read_only_fields = ['id', 'citizen', 'status', 'created_at']

    def validate_title(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value.strip()

    def validate_description(self, value):
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Description must be at least 5 characters.")
        return value.strip()

    def _get_or_create_category(self, category_data):
        """
        Accept either:
          - {"name": "Water"}  OR
          - an integer id passed in place of nested dict (handled upstream if needed)
        """
        if isinstance(category_data, dict):
            name = category_data.get('name', '').strip()
            if not name:
                return None
            category, _ = Category.objects.get_or_create(name=name)
            return category
        return None

    def create(self, validated_data):
        category_data = validated_data.pop('category', None)
        if category_data:
            category = self._get_or_create_category(category_data)
            validated_data['category'] = category

        user = self.context['request'].user
        grievance = Grievance.objects.create(citizen=user, **validated_data)
        return grievance

    def update(self, instance, validated_data):
        # allow updating title/description/status depending on caller permissions in view
        for attr, value in validated_data.items():
            # ignore attempts to set citizen/created_at/id
            if attr in ('citizen', 'created_at', 'id'):
                continue
            setattr(instance, attr, value)
        instance.save()
        return instance

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'grievance', 'rating', 'comments', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_rating(self, value):
        if value is None:
            return 0
        if not (0 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 0 and 5.")
        return value

class RegisterSerializer(serializers.ModelSerializer):
    """
    Public registration — always creates a normal Django User.
    Role (citizen/officer/admin) should be set only by admin endpoints or via Django admin.
    """
    email = serializers.EmailField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # If you use a UserProfile signal it will create the profile automatically.
        return user

