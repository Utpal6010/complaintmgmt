from django.contrib import admin
from django.utils.html import format_html

from hello_world.support.models import Complaint, ComplaintComment, SupportProfile, AuditLog


@admin.register(SupportProfile)
class SupportProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_active", "department", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__username", "department")


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("title", "status_badge", "priority_badge", "creator", "assigned_to", "overdue_badge", "sla_due_date")
    list_filter = ("status", "priority", "is_overdue", "created_at")
    search_fields = ("title", "description", "creator__username", "assigned_to__username")
    readonly_fields = ("created_at", "updated_at", "resolution_date", "resolution_time_hours")
    fieldsets = (
        ("Complaint Details", {
            "fields": ("title", "description", "category", "priority")
        }),
        ("Assignment", {
            "fields": ("creator", "assigned_to", "manager")
        }),
        ("Status & SLA", {
            "fields": ("status", "sla_due_date", "is_overdue", "resolution_date", "resolution_time_hours")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "new": "#0066cc",
            "open": "#ff9900",
            "in_progress": "#ffc400",
            "resolved": "#009900",
            "closed": "#666666",
        }
        color = colors.get(obj.status, "#000")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def priority_badge(self, obj):
        colors = {
            "low": "#00aa00",
            "medium": "#ffaa00",
            "high": "#ff6600",
            "critical": "#cc0000",
        }
        color = colors.get(obj.priority, "#000")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = "Priority"

    def overdue_badge(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠ OVERDUE</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    overdue_badge.short_description = "SLA Status"


@admin.register(ComplaintComment)
class ComplaintCommentAdmin(admin.ModelAdmin):
    list_display = ("complaint", "author", "created_at")
    search_fields = ("complaint__title", "author__username", "text")
    readonly_fields = ("created_at",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("complaint", "user", "action", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("complaint__title", "user__username")
    readonly_fields = ("timestamp",)

