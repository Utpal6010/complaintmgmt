from rest_framework import serializers
from django.contrib.auth.models import User

from hello_world.support.models import Complaint, ComplaintComment, SupportProfile, AuditLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class SupportProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = SupportProfile
        fields = ["id", "user", "role", "is_active", "department", "phone", "created_at"]


class ComplaintCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = ComplaintComment
        fields = ["id", "complaint", "author", "text", "created_at"]
        read_only_fields = ["author", "created_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "complaint", "user", "action", "old_value", "new_value", "timestamp"]


class ComplaintDetailSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    manager = UserSerializer(read_only=True)
    comments = ComplaintCommentSerializer(many=True, read_only=True)
    audit_logs = AuditLogSerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id",
            "title",
            "description",
            "category",
            "priority",
            "status",
            "creator",
            "assigned_to",
            "manager",
            "sla_due_date",
            "is_overdue",
            "resolution_date",
            "resolution_time_hours",
            "created_at",
            "updated_at",
            "comments",
            "audit_logs",
        ]


class ComplaintListSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    manager = UserSerializer(read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id",
            "title",
            "priority",
            "status",
            "creator",
            "assigned_to",
            "manager",
            "sla_due_date",
            "is_overdue",
            "created_at",
            "updated_at",
        ]


class ComplaintCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ["title", "description", "category", "priority", "assigned_to", "status"]
