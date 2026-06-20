from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta


class SupportProfile(models.Model):
    ROLE_OWNER = "owner"
    ROLE_MANAGER = "manager"
    ROLE_PARTNER = "partner"
    ROLE_ENGINEER = "engineer"

    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner / Admin"),
        (ROLE_MANAGER, "Manager"),
        (ROLE_PARTNER, "Partner"),
        (ROLE_ENGINEER, "Support Engineer"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="support_profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_owner(self):
        return self.role == self.ROLE_OWNER

    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER

    @property
    def is_partner(self):
        return self.role == self.ROLE_PARTNER

    @property
    def is_engineer(self):
        return self.role == self.ROLE_ENGINEER


class Complaint(models.Model):
    STATUS_NEW = "new"
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CLOSED, "Closed"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CRITICAL = "critical"

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_CRITICAL, "Critical"),
    ]

    # Core complaint fields
    title = models.CharField(max_length=220)
    description = models.TextField()
    category = models.CharField(max_length=100, default="General", blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)

    # Customer Details
    customer_name = models.CharField(max_length=150, default="")
    customer_phone = models.CharField(max_length=20, default="")
    customer_address = models.TextField(default="")

    # AC Details
    ac_brand = models.CharField(max_length=100, default="")
    ac_model = models.CharField(max_length=100, default="")
    ac_capacity = models.CharField(max_length=50, default="", blank=True)  # e.g., "1.5 Ton Split"
    purchase_date = models.DateField(null=True, blank=True)
    is_under_warranty = models.BooleanField(default=True)
    sold_by = models.CharField(max_length=150, blank=True, default="")

    # Users
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_complaints")
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_complaints")
    manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_complaints")

    # Status & Workflow
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_NEW)
    
    # SLA Tracking
    sla_due_date = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    resolution_date = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["creator", "status"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["sla_due_date"]),
            models.Index(fields=["is_overdue"]),
        ]

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        # Set SLA due date on creation
        if not self.sla_due_date:
            self.sla_due_date = timezone.now() + timedelta(hours=48)
        
        # Mark resolution date when closed
        if self.status == self.STATUS_CLOSED and not self.resolution_date:
            self.resolution_date = timezone.now()
        
        # Check if overdue
        self.is_overdue = timezone.now() > self.sla_due_date and self.status != self.STATUS_CLOSED
        
        super().save(*args, **kwargs)

    def can_view(self, user):
        if not user.is_authenticated:
            return False
        profile = getattr(user, "support_profile", None)
        if profile is None:
            return False
        if profile.is_owner or profile.is_manager:
            return True
        if self.creator == user:
            return True
        if self.assigned_to == user:
            return True
        return False

    @property
    def resolution_time_hours(self):
        if self.resolution_date:
            return round((self.resolution_date - self.created_at).total_seconds() / 3600, 2)
        return None

    @property
    def days_remaining(self):
        """Days until SLA deadline"""
        if self.status == self.STATUS_CLOSED:
            return 0
        remaining = (self.sla_due_date - timezone.now()).total_seconds() / (24 * 3600)
        return max(0, round(remaining, 1))


class ComplaintComment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="complaint_comments")
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.complaint.title}"


class AuditLog(models.Model):
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_CLOSE = "close"
    ACTION_COMMENT = "comment"
    ACTION_ASSIGN = "assign"

    ACTION_CHOICES = [
        (ACTION_CREATE, "Created"),
        (ACTION_UPDATE, "Updated"),
        (ACTION_CLOSE, "Closed"),
        (ACTION_COMMENT, "Comment Added"),
        (ACTION_ASSIGN, "Assigned"),
    ]

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="audit_logs")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="audit_logs")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} on {self.complaint.title} by {self.user.username}"

