from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from hello_world.support.forms import ComplaintCommentForm, ComplaintForm, SupportUserCreationForm
from hello_world.support.models import Complaint, ComplaintComment, SupportProfile


def index(request):
    if request.user.is_authenticated:
        return redirect("support:dashboard")
    return render(request, "support/index.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("support:dashboard")
    if request.method == "POST":
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("support:dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "support/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("support:login")


def _require_role(user, roles):
    profile = getattr(user, "support_profile", None)
    if profile is None or profile.role not in roles:
        raise Http404
    return profile


@login_required
def dashboard(request):
    profile = getattr(request.user, "support_profile", None)
    if profile is None:
        messages.error(request, "Your account needs a role before you can use the support portal.")
        return redirect("support:login")

    if profile.is_owner or profile.is_manager:
        complaints = Complaint.objects.order_by("-updated_at")
    elif profile.is_partner:
        complaints = Complaint.objects.filter(creator=request.user).order_by("-updated_at")
    else:
        complaints = Complaint.objects.filter(assigned_to=request.user).order_by("-updated_at")

    return render(request, "support/dashboard.html", {
        "profile": profile,
        "complaints": complaints,
    })


@login_required
def complaint_list(request):
    profile = getattr(request.user, "support_profile", None)
    if profile is None:
        raise Http404
    if profile.is_owner or profile.is_manager:
        complaints = Complaint.objects.order_by("-updated_at")
    elif profile.is_partner:
        complaints = Complaint.objects.filter(creator=request.user).order_by("-updated_at")
    else:
        complaints = Complaint.objects.filter(assigned_to=request.user).order_by("-updated_at")
    return render(request, "support/complaint_list.html", {"complaints": complaints, "profile": profile})


@login_required
def complaint_create(request):
    profile = getattr(request.user, "support_profile", None)
    if profile is None or not (profile.is_owner or profile.is_manager or profile.is_partner):
        raise Http404

    if request.method == "POST":
        form = ComplaintForm(request.POST, user=request.user)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.creator = request.user
            if profile.is_manager:
                complaint.manager = request.user
            complaint.save()
            messages.success(request, "Complaint created successfully.")
            return redirect("support:complaint_detail", pk=complaint.pk)
    else:
        form = ComplaintForm(user=request.user)
    return render(request, "support/complaint_form.html", {"form": form, "profile": profile})


@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if not complaint.can_view(request.user):
        raise Http404

    profile = getattr(request.user, "support_profile", None)
    if profile is None:
        raise Http404

    comment_form = ComplaintCommentForm()
    if request.method == "POST":
        if "comment" in request.POST:
            comment_form = ComplaintCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.complaint = complaint
                comment.author = request.user
                comment.save()
                messages.success(request, "Comment added.")
                return redirect("support:complaint_detail", pk=complaint.pk)
        elif "status" in request.POST and (profile.is_owner or profile.is_manager or profile.is_engineer):
            status = request.POST.get("status")
            if status in dict(Complaint.STATUS_CHOICES):
                complaint.status = status
                complaint.save()
                messages.success(request, "Complaint status updated.")
                return redirect("support:complaint_detail", pk=complaint.pk)
        elif "assign" in request.POST and (profile.is_owner or profile.is_manager):
            assigned_id = request.POST.get("assigned_to")
            if assigned_id:
                assigned_user = get_object_or_404(User, pk=assigned_id)
                if getattr(assigned_user, "support_profile", None) and assigned_user.support_profile.is_engineer:
                    complaint.assigned_to = assigned_user
                    complaint.manager = request.user
                    complaint.save()
                    messages.success(request, "Complaint assigned.")
                    return redirect("support:complaint_detail", pk=complaint.pk)
    engineers = User.objects.filter(support_profile__role=SupportProfile.ROLE_ENGINEER)
    comments = complaint.comments.order_by("created_at")
    return render(request, "support/complaint_detail.html", {
        "complaint": complaint,
        "profile": profile,
        "comment_form": comment_form,
        "engineers": engineers,
        "comments": comments,
        "status_choices": Complaint.STATUS_CHOICES,
    })


@login_required
def user_create(request):
    profile = _require_role(request.user, [SupportProfile.ROLE_OWNER, SupportProfile.ROLE_MANAGER])
    allowed_roles = [SupportProfile.ROLE_ENGINEER, SupportProfile.ROLE_PARTNER]
    if profile.is_owner:
        allowed_roles = [SupportProfile.ROLE_OWNER, SupportProfile.ROLE_MANAGER, SupportProfile.ROLE_ENGINEER, SupportProfile.ROLE_PARTNER]

    if request.method == "POST":
        form = SupportUserCreationForm(request.POST, allowed_roles=allowed_roles)
        if form.is_valid():
            new_user = form.save()
            messages.success(request, f"User {new_user.username} created.")
            return redirect("support:dashboard")
    else:
        form = SupportUserCreationForm(allowed_roles=allowed_roles)

    return render(request, "support/user_form.html", {"form": form, "profile": profile})
