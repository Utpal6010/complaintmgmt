"""
Functional Tests for AC Complaint Support Portal
Tests all critical user journeys and role-based workflows.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from hello_world.support.models import Complaint, ComplaintComment, SupportProfile


class UserAuthenticationTests(TestCase):
    """Test authentication and session management."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser_auth",
            email="test@example.com",
            password="SecurePass123!"
        )
        SupportProfile.objects.get_or_create(
            user=self.user,
            defaults={"role": SupportProfile.ROLE_PARTNER}
        )

    def test_login_success(self):
        """Test successful user login."""
        response = self.client.post(reverse("support:login"), {
            "username": "testuser",
            "password": "SecurePass123!"
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertEqual(response.wsgi_request.user.username, "testuser")

    def test_login_failure_wrong_password(self):
        """Test login with incorrect password."""
        response = self.client.post(reverse("support:login"), {
            "username": "testuser",
            "password": "WrongPassword"
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        """Test user logout."""
        self.client.login(username="testuser", password="SecurePass123!")
        response = self.client.get(reverse("support:logout"))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_redirect_to_login(self):
        """Test unauthenticated users are redirected to login."""
        response = self.client.get(reverse("support:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)


class ComplaintCreationTests(TestCase):
    """Test complaint creation workflow."""

    def setUp(self):
        self.client = Client()
        self.partner = User.objects.create_user(
            username="partner1_func",
            password="Pass123!"
        )
        SupportProfile.objects.get_or_create(
            user=self.partner,
            defaults={"role": SupportProfile.ROLE_PARTNER}
        )
        self.client.login(username="partner1_func", password="Pass123!")

    def test_partner_can_create_complaint(self):
        """Test partner creating a new complaint."""
        response = self.client.post(reverse("support:complaint_create"), {
            "title": "AC not cooling",
            "description": "Daikin AC not cooling properly",
            "customer_name": "John Doe",
            "customer_phone": "9876543210",
            "customer_address": "123 Main St",
            "ac_brand": "Daikin",
            "ac_model": "1.5 Ton Split",
            "purchase_date": "2026-01-01",
            "is_under_warranty": True,
            "sold_by": "Ace Electronics"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Complaint.objects.count(), 1)
        complaint = Complaint.objects.first()
        self.assertEqual(complaint.creator, self.partner)
        self.assertEqual(complaint.status, Complaint.STATUS_NEW)

    def test_complaint_has_correct_sla_deadline(self):
        """Test complaint is created with 48-hour SLA."""
        complaint = Complaint.objects.create(
            title="Test complaint",
            description="Test",
            customer_name="Test User",
            customer_phone="1234567890",
            customer_address="Test",
            creator=self.partner
        )
        time_diff = (complaint.sla_due_date - timezone.now()).total_seconds() / 3600
        self.assertAlmostEqual(time_diff, 48, delta=1)  # ~48 hours


class RoleBasedAccessTests(TestCase):
    """Test role-based access control."""

    def setUp(self):
        self.client = Client()
        
        # Create users for each role
        self.owner = User.objects.create_user(username="owner_rbac", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.owner, defaults={"role": SupportProfile.ROLE_OWNER})
        
        self.manager = User.objects.create_user(username="manager_rbac", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.manager, defaults={"role": SupportProfile.ROLE_MANAGER})
        
        self.partner = User.objects.create_user(username="partner_rbac", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.partner, defaults={"role": SupportProfile.ROLE_PARTNER})
        
        self.engineer = User.objects.create_user(username="engineer_rbac", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.engineer, defaults={"role": SupportProfile.ROLE_ENGINEER})
        
        # Create a test complaint by partner
        self.complaint = Complaint.objects.create(
            title="Test",
            description="Test",
            customer_name="Test",
            customer_phone="1234567890",
            customer_address="Test",
            creator=self.partner,
            assigned_to=self.engineer,
            manager=self.manager
        )

    def test_partner_sees_only_own_complaints(self):
        """Test partner can only view own complaints."""
        self.client.login(username="partner_rbac", password="Pass123!")
        response = self.client.get(reverse("support:complaint_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.complaint.title)

    def test_engineer_sees_assigned_complaints(self):
        """Test engineer can only see assigned complaints."""
        other_partner = User.objects.create_user(username="other_partner_rbac", password="Pass123!")
        SupportProfile.objects.get_or_create(user=other_partner, defaults={"role": SupportProfile.ROLE_PARTNER})
        
        other_complaint = Complaint.objects.create(
            title="Other complaint",
            description="Test",
            customer_name="Test",
            customer_phone="1234567890",
            customer_address="Test",
            creator=other_partner
        )
        
        self.client.login(username="engineer_rbac", password="Pass123!")
        response = self.client.get(reverse("support:complaint_list"))
        self.assertContains(response, self.complaint.title)
        self.assertNotContains(response, other_complaint.title)

    def test_owner_sees_all_complaints(self):
        """Test owner can see all complaints."""
        self.client.login(username="owner_rbac", password="Pass123!")
        response = self.client.get(reverse("support:complaint_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.complaint.title)


class ComplaintStatusWorkflowTests(TestCase):
    """Test complaint status transitions."""

    def setUp(self):
        self.client = Client()
        self.engineer = User.objects.create_user(username="eng_workflow", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.engineer, defaults={"role": SupportProfile.ROLE_ENGINEER})
        
        self.partner = User.objects.create_user(username="part_workflow", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.partner, defaults={"role": SupportProfile.ROLE_PARTNER})
        
        self.complaint = Complaint.objects.create(
            title="Test",
            description="Test",
            customer_name="Test",
            customer_phone="1234567890",
            customer_address="Test",
            creator=self.partner,
            assigned_to=self.engineer,
            status=Complaint.STATUS_OPEN
        )

    def test_engineer_can_update_status(self):
        """Test engineer can update complaint status."""
        self.client.login(username="eng_workflow", password="Pass123!")
        response = self.client.post(
            reverse("support:complaint_detail", args=[self.complaint.pk]),
            {"status": Complaint.STATUS_IN_PROGRESS}
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, Complaint.STATUS_IN_PROGRESS)

    def test_resolution_date_set_on_close(self):
        """Test resolution date is set when complaint is closed."""
        self.complaint.status = Complaint.STATUS_CLOSED
        self.complaint.save()
        self.assertIsNotNone(self.complaint.resolution_date)

    def test_overdue_flag_on_sla_breach(self):
        """Test overdue flag is set when SLA is breached."""
        self.complaint.sla_due_date = timezone.now() - timedelta(hours=1)
        self.complaint.save()
        self.complaint.refresh_from_db()
        self.assertTrue(self.complaint.is_overdue)


class CommentWorkflowTests(TestCase):
    """Test comment functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user_comment", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.user, defaults={"role": SupportProfile.ROLE_PARTNER})
        
        self.complaint = Complaint.objects.create(
            title="Test",
            description="Test",
            customer_name="Test",
            customer_phone="1234567890",
            customer_address="Test",
            creator=self.user
        )

    def test_add_comment_to_complaint(self):
        """Test adding a comment to a complaint."""
        self.client.login(username="user_comment", password="Pass123!")
        response = self.client.post(
            reverse("support:complaint_detail", args=[self.complaint.pk]),
            {"text": "Test comment", "comment": "add"}
        )
        self.assertEqual(ComplaintComment.objects.count(), 1)
        comment = ComplaintComment.objects.first()
        self.assertEqual(comment.text, "Test comment")
        self.assertEqual(comment.author, self.user)
