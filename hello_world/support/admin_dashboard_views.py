from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, F, DurationField
from django.utils import timezone
from datetime import timedelta

from hello_world.support.models import Complaint, SupportProfile


@login_required
def admin_dashboard(request):
    """Admin/Manager dashboard with metrics."""
    profile = getattr(request.user, "support_profile", None)
    
    if not profile or not (profile.is_owner or profile.is_manager):
        return redirect("support:dashboard")

    # Get all complaints for metrics
    all_complaints = Complaint.objects.all()
    
    # Status breakdown
    new_count = all_complaints.filter(status=Complaint.STATUS_NEW).count()
    open_count = all_complaints.filter(status=Complaint.STATUS_OPEN).count()
    in_progress_count = all_complaints.filter(status=Complaint.STATUS_IN_PROGRESS).count()
    resolved_count = all_complaints.filter(status=Complaint.STATUS_RESOLVED).count()
    closed_count = all_complaints.filter(status=Complaint.STATUS_CLOSED).count()
    
    # Aggregate metrics
    total_complaints = all_complaints.count()
    active_complaints = all_complaints.filter(status__in=[Complaint.STATUS_NEW, Complaint.STATUS_OPEN, Complaint.STATUS_IN_PROGRESS]).count()
    overdue_complaints = all_complaints.filter(is_overdue=True).count()
    
    # SLA Performance
    closed_with_resolution = all_complaints.filter(status=Complaint.STATUS_CLOSED, resolution_date__isnull=False)
    avg_resolution_hours = closed_with_resolution.aggregate(
        avg_hours=Avg(F("resolution_date") - F("created_at"), output_field=DurationField())
    )
    avg_hours_value = None
    if avg_resolution_hours["avg_hours"]:
        avg_hours_value = round(avg_resolution_hours["avg_hours"].total_seconds() / 3600, 1)
    
    # Priority breakdown
    priority_breakdown = {
        "critical": all_complaints.filter(priority=Complaint.PRIORITY_CRITICAL).count(),
        "high": all_complaints.filter(priority=Complaint.PRIORITY_HIGH).count(),
        "medium": all_complaints.filter(priority=Complaint.PRIORITY_MEDIUM).count(),
        "low": all_complaints.filter(priority=Complaint.PRIORITY_LOW).count(),
    }
    
    # Engineer workload
    engineers = SupportProfile.objects.filter(
        role=SupportProfile.ROLE_ENGINEER,
        is_active=True
    ).select_related("user")
    
    engineer_stats = []
    for eng_profile in engineers:
        open_cases = Complaint.objects.filter(
            assigned_to=eng_profile.user,
            status__in=[Complaint.STATUS_NEW, Complaint.STATUS_OPEN, Complaint.STATUS_IN_PROGRESS]
        ).count()
        closed_cases = Complaint.objects.filter(
            assigned_to=eng_profile.user,
            status=Complaint.STATUS_CLOSED
        ).count()
        
        engineer_stats.append({
            "name": eng_profile.user.get_full_name() or eng_profile.user.username,
            "open": open_cases,
            "closed": closed_cases,
            "total": open_cases + closed_cases,
        })
    
    # Recent complaints
    recent_complaints = all_complaints.order_by("-created_at")[:10]
    
    # Overdue complaints
    overdue_list = all_complaints.filter(is_overdue=True).order_by("sla_due_date")[:5]
    
    # SLA compliance rate
    closed_on_time = closed_with_resolution.filter(resolution_date__lte=F("sla_due_date")).count()
    sla_compliance_rate = 0
    if closed_with_resolution.count() > 0:
        sla_compliance_rate = round((closed_on_time / closed_with_resolution.count()) * 100, 1)
    
    context = {
        "profile": profile,
        "total_complaints": total_complaints,
        "active_complaints": active_complaints,
        "overdue_complaints": overdue_complaints,
        "closed_complaints": closed_count,
        "avg_resolution_hours": avg_hours_value,
        "sla_compliance_rate": sla_compliance_rate,
        "status_breakdown": {
            "new": new_count,
            "open": open_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "closed": closed_count,
        },
        "priority_breakdown": priority_breakdown,
        "engineer_stats": engineer_stats,
        "recent_complaints": recent_complaints,
        "overdue_complaints_list": overdue_list,
    }
    
    return render(request, "support/admin_dashboard.html", context)
