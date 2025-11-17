# adminpanel/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from adminpanel.models import (
    Department,
    Category,
    Grievance,
    GrievanceRemark,
    Feedback,
    ChangeLog,
)

User = get_user_model()


# ------------------------
# Small helper serializers
# ------------------------
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name", "code")


class CategorySerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Category
        fields = ("id", "name", "department", "department_id")


class SimpleUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "first_name", "last_name", "email")

    def get_full_name(self, obj):
        # handle both User.get_full_name and fallback
        try:
            return obj.get_full_name()
        except Exception:
            return f"{getattr(obj, 'first_name', '')} {getattr(obj, 'last_name', '')}".strip()


# ------------------------
# Remark & Feedback
# ------------------------
class GrievanceRemarkSerializer(serializers.ModelSerializer):
    officer = SimpleUserSerializer(read_only=True)
    officer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="officer", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = GrievanceRemark
        fields = ("id", "grievance", "officer", "officer_id", "remark", "created_at")
        read_only_fields = ("id", "created_at", "officer")


class FeedbackSerializer(serializers.ModelSerializer):
    grievance = serializers.PrimaryKeyRelatedField(queryset=Grievance.objects.all())

    class Meta:
        model = Feedback
        fields = ("id", "grievance", "rating", "comments", "submitted_at")
        read_only_fields = ("id", "submitted_at")


# ------------------------
# Grievance serializers
# ------------------------
class GrievanceListSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    assigned_officer = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Grievance
        fields = (
            "id",
            "tracking_id",
            "title",
            "description",
            "status",
            "category",
            "department",
            "user",
            "assigned_officer",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("tracking_id", "created_at", "updated_at")


class GrievanceDetailSerializer(GrievanceListSerializer):
    remarks = GrievanceRemarkSerializer(many=True, read_only=True)
    feedback = FeedbackSerializer(read_only=True)

    class Meta(GrievanceListSerializer.Meta):
        fields = GrievanceListSerializer.Meta.fields + ("remarks", "feedback")


class GrievanceCreateUpdateSerializer(serializers.ModelSerializer):
    # accept FK ids from client for writes
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", required=False, allow_null=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", required=False, allow_null=True
    )
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department", required=False, allow_null=True
    )
    assigned_officer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="assigned_officer", required=False, allow_null=True
    )

    class Meta:
        model = Grievance
        fields = (
            "id",
            "tracking_id",
            "user_id",
            "title",
            "description",
            "category_id",
            "department_id",
            "attached_file",
            "assigned_officer_id",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("tracking_id", "created_at", "updated_at")

    def validate_status(self, value):
        allowed = {c[0] for c in Grievance.STATUS_CHOICES}
        if value not in allowed:
            raise serializers.ValidationError("Invalid status value.")
        return value

    def create(self, validated_data):
        # If you want to force the creating user: validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # You can inspect changes here and create ChangeLog entries in the view if needed
        return super().update(instance, validated_data)


# ------------------------
# ChangeLog serializer (optional)
# ------------------------
class ChangeLogSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ChangeLog
        fields = ("id", "user", "grievance", "action", "before", "after", "timestamp")
        read_only_fields = fields
