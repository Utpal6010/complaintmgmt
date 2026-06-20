from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.contrib.auth.models import User

from hello_world.support.models import Complaint, ComplaintComment, SupportProfile, AuditLog
from hello_world.support.serializers import (
    ComplaintListSerializer,
    ComplaintDetailSerializer,
    ComplaintCreateUpdateSerializer,
    ComplaintCommentSerializer,
    SupportProfileSerializer,
    AuditLogSerializer,
)


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class ComplaintViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "description", "category"]
    ordering_fields = ["created_at", "sla_due_date", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, "support_profile", None)

        if not profile:
            return Complaint.objects.none()

        if profile.is_owner or profile.is_manager:
            return Complaint.objects.all()
        elif profile.is_partner:
            return Complaint.objects.filter(creator=user)
        elif profile.is_engineer:
            return Complaint.objects.filter(assigned_to=user)
        else:
            return Complaint.objects.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ComplaintDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ComplaintCreateUpdateSerializer
        return ComplaintListSerializer

    def perform_create(self, serializer):
        complaint = serializer.save(creator=self.request.user)
        AuditLog.objects.create(
            complaint=complaint,
            user=self.request.user,
            action=AuditLog.ACTION_CREATE,
            new_value={"title": complaint.title, "status": complaint.status},
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        old_status = instance.status
        complaint = serializer.save()

        if old_status != complaint.status:
            AuditLog.objects.create(
                complaint=complaint,
                user=self.request.user,
                action=AuditLog.ACTION_UPDATE,
                old_value={"status": old_status},
                new_value={"status": complaint.status},
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_comment(self, request, pk=None):
        complaint = self.get_object()
        serializer = ComplaintCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(complaint=complaint, author=request.user)
            AuditLog.objects.create(
                complaint=complaint,
                user=request.user,
                action=AuditLog.ACTION_COMMENT,
                new_value={"text": serializer.data["text"][:100]},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def dashboard_stats(self, request):
        """Return dashboard statistics for admin/manager."""
        profile = getattr(request.user, "support_profile", None)
        if not profile or not (profile.is_owner or profile.is_manager):
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN,
            )

        complaints = Complaint.objects.all()
        return Response(
            {
                "total_complaints": complaints.count(),
                "open_complaints": complaints.filter(status__in=["new", "open", "in_progress"]).count(),
                "closed_complaints": complaints.filter(status="closed").count(),
                "overdue_complaints": complaints.filter(is_overdue=True).count(),
                "by_priority": {
                    "critical": complaints.filter(priority="critical").count(),
                    "high": complaints.filter(priority="high").count(),
                    "medium": complaints.filter(priority="medium").count(),
                    "low": complaints.filter(priority="low").count(),
                },
                "by_status": {
                    "new": complaints.filter(status="new").count(),
                    "open": complaints.filter(status="open").count(),
                    "in_progress": complaints.filter(status="in_progress").count(),
                    "resolved": complaints.filter(status="resolved").count(),
                    "closed": complaints.filter(status="closed").count(),
                },
            }
        )

    @action(detail=False, methods=["get"])
    def engineer_workload(self, request):
        """Return workload distribution across engineers."""
        profile = getattr(request.user, "support_profile", None)
        if not profile or not (profile.is_owner or profile.is_manager):
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN,
            )

        engineers = User.objects.filter(
            support_profile__role=SupportProfile.ROLE_ENGINEER,
            support_profile__is_active=True,
        )
        workload = []
        for engineer in engineers:
            open_count = engineer.assigned_complaints.filter(
                status__in=["new", "open", "in_progress"]
            ).count()
            closed_count = engineer.assigned_complaints.filter(status="closed").count()
            workload.append(
                {
                    "engineer": engineer.username,
                    "open": open_count,
                    "closed": closed_count,
                    "total": open_count + closed_count,
                }
            )
        return Response(workload)


class SupportProfileViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SupportProfileSerializer

    def get_queryset(self):
        profile = getattr(self.request.user, "support_profile", None)
        if profile and (profile.is_owner or profile.is_manager):
            return SupportProfile.objects.filter(is_active=True)
        return SupportProfile.objects.filter(user=self.request.user)


class ComplaintCommentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ComplaintCommentSerializer

    def get_queryset(self):
        return ComplaintComment.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AuditLogSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]

    def get_queryset(self):
        profile = getattr(self.request.user, "support_profile", None)
        if profile and (profile.is_owner or profile.is_manager):
            return AuditLog.objects.all()
        # Partners and engineers can only see logs for their own complaints
        return AuditLog.objects.filter(
            complaint__creator=self.request.user
        ) | AuditLog.objects.filter(complaint__assigned_to=self.request.user)
