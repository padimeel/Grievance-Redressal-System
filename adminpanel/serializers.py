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


# Small helpers
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name", "code")


class SimpleUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "first_name", "last_name", "email")

    def get_full_name(self, obj):
        return (obj.get_full_name() or f"{obj.first_name} {obj.last_name}".strip())


# Category serializer
class CategorySerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source="department",
        write_only=True,
        required=False,
        allow_null=True,
    )
    department_name = serializers.CharField(source="department.name", read_only=True)

    grievance_count = serializers.IntegerField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True, required=False)
    updated_at = serializers.DateTimeField(read_only=True, required=False)

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "department",
            "department_id",
            "department_name",
            "grievance_count",
            "created_at",
            "updated_at",
        )


# Remark & Feedback
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

    def validate_grievance(self, value):
        if getattr(value, "status", None) != Grievance.STATUS_RESOLVED:
            raise serializers.ValidationError("Feedback can only be submitted for resolved grievances.")
        return value


# Grievance list/detail
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


# Grievance create/update - accepts department_id OR department_name
class GrievanceCreateUpdateSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", required=False, allow_null=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source="category", required=False, allow_null=True)

    # prefer numeric FK writes:
    department_id = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), source="department", required=False, allow_null=True)
    # also accept a name (string). If provided and no matching dept exists, we create it (you can change to raise error).
    department_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    department = DepartmentSerializer(read_only=True)
    assigned_officer_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="assigned_officer", required=False, allow_null=True)
    assigned_officer = SimpleUserSerializer(read_only=True)
    attached_file = serializers.FileField(required=False, allow_null=True)

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
            "department_name",
            "department",
            "attached_file",
            "assigned_officer_id",
            "assigned_officer",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("tracking_id", "created_at", "updated_at")

    def validate_status(self, value):
        allowed = {c[0] for c in getattr(Grievance, "STATUS_CHOICES", [])}
        if value not in allowed:
            raise serializers.ValidationError("Invalid status value.")
        return value

    def validate(self, attrs):
        # If department_name provided, and department wasn't already set via department_id,
        # find (case-insensitive) or create the Department instance.
        dept_name = attrs.pop("department_name", None)
        if dept_name and not attrs.get("department"):
            name_clean = str(dept_name).strip()
            if name_clean:
                dept = Department.objects.filter(name__iexact=name_clean).first()
                if not dept:
                    # Auto-create department. If you'd rather reject unknown names, replace with a ValidationError.
                    dept = Department.objects.create(name=name_clean)
                attrs["department"] = dept
        return attrs


# ChangeLog
class ChangeLogSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ChangeLog
        fields = ("id", "user", "grievance", "action", "before", "after", "timestamp")
        read_only_fields = ("id", "user", "grievance", "action", "before", "after", "timestamp")
