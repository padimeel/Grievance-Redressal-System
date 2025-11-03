from rest_framework import serializers
from .models import Category, Grievance, Feedback

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class GrievanceSerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    class Meta:
        model = Grievance
        fields = ['id', 'citizen', 'category', 'title', 'description', 'status', 'created_at']
        read_only_fields = ['citizen', 'status', 'created_at']

    def create(self, validated_data):
        category_data = validated_data.pop('category', None)
        if category_data:
            category, _ = Category.objects.get_or_create(name=category_data['name'])
            validated_data['category'] = category

        user = self.context['request'].user
        grievance = Grievance.objects.create(citizen=user, **validated_data)
        return grievance


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'grievance', 'rating', 'comments', 'created_at']
