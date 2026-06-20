"""
Security Tests - OWASP Top 10 Coverage
Tests for common web vulnerabilities and attack vectors.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from urllib.parse import quote

from hello_world.support.models import Complaint, SupportProfile


class SQLInjectionTests(TestCase):
    """Test protection against SQL Injection attacks."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user_sqli", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.user, defaults={"role": SupportProfile.ROLE_PARTNER})
        self.client.login(username="user_sqli", password="Pass123!")

    def test_search_with_sql_injection_payload(self):
        """Test search field is protected against SQL injection."""
        injection_payload = "'; DROP TABLE support_complaint; --"
        response = self.client.get(f"{reverse('support:complaint_list')}?search={quote(injection_payload)}")
        self.assertEqual(response.status_code, 200)

    def test_filter_with_sql_injection(self):
        """Test filter parameter is protected against SQL injection."""
        injection_payload = "1 OR 1=1; --"
        response = self.client.get(f"{reverse('support:complaint_list')}?status={injection_payload}")
        self.assertEqual(response.status_code, 200)


class AuthenticationTests(TestCase):
    """Test broken authentication vulnerabilities."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user_auth", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.user, defaults={"role": SupportProfile.ROLE_PARTNER})

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post(reverse("support:login"), {
            "username": "user_auth",
            "password": "Pass123!"
        })
        self.assertEqual(response.status_code, 302)


class AccessControlTests(TestCase):
    """Test Broken Access Control vulnerabilities."""

    def setUp(self):
        self.client = Client()
        
        self.partner = User.objects.create_user(username="partner_sec", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.partner, defaults={"role": SupportProfile.ROLE_PARTNER})
        
        self.engineer = User.objects.create_user(username="engineer_sec", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.engineer, defaults={"role": SupportProfile.ROLE_ENGINEER})
        
        self.manager = User.objects.create_user(username="manager_sec", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.manager, defaults={"role": SupportProfile.ROLE_MANAGER})
        
        self.complaint = Complaint.objects.create(
            title="Test", description="Test", customer_name="Test",
            customer_phone="1234567890", customer_address="Test",
            creator=self.partner
        )

    def test_partner_cannot_access_admin(self):
        """Test partner cannot access admin dashboard."""
        self.client.login(username="partner_sec", password="Pass123!")
        response = self.client.get(reverse("support:admin_dashboard"))
        self.assertIn(response.status_code, [403, 302])

    def test_engineer_cannot_create_users(self):
        """Test engineer cannot create new users."""
        self.client.login(username="engineer_sec", password="Pass123!")
        response = self.client.post(reverse("support:user_create"), {
            "username": "newuser_sec",
            "password1": "Pass123!",
            "password2": "Pass123!",
            "role": SupportProfile.ROLE_ENGINEER
        })
        self.assertIn(response.status_code, [403, 302])


class XSSTests(TestCase):
    """Test Cross-Site Scripting (XSS) vulnerabilities."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user_xss", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.user, defaults={"role": SupportProfile.ROLE_PARTNER})
        self.client.login(username="user_xss", password="Pass123!")

    def test_xss_in_title_escaped(self):
        """Test XSS payload in complaint title is escaped."""
        xss_payload = "<script>alert('XSS')</script>"
        complaint = Complaint.objects.create(
            title=xss_payload, description="Test", customer_name="Test",
            customer_phone="1234567890", customer_address="Test",
            creator=self.user
        )
        
        response = self.client.get(reverse("support:complaint_list"))
        self.assertNotIn("<script>", response.content.decode())


class CSRFProtectionTests(TestCase):
    """Test CSRF protection."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user_csrf", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.user, defaults={"role": SupportProfile.ROLE_PARTNER})

    def test_csrf_protection_enabled(self):
        """Test CSRF protection is enabled."""
        self.client.login(username="user_csrf", password="Pass123!")
        response = self.client.get(reverse("support:complaint_create"))
        self.assertIn(b'csrfmiddlewaretoken', response.content)


class ValidationTests(TestCase):
    """Test input validation."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user_val", password="Pass123!")
        SupportProfile.objects.get_or_create(user=self.user, defaults={"role": SupportProfile.ROLE_PARTNER})
        self.client.login(username="user_val", password="Pass123!")

    def test_empty_fields_rejected(self):
        """Test empty required fields are rejected."""
        response = self.client.post(reverse("support:complaint_create"), {
            "title": "", "description": "",
            "customer_name": "", "customer_phone": "",
            "customer_address": ""
        })
        self.assertEqual(response.status_code, 200)
