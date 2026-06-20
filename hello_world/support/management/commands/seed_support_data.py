from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from hello_world.support.models import Complaint, ComplaintComment, SupportProfile


class Command(BaseCommand):
    help = "Seed support portal dummy users, complaints, and comments."

    def handle(self, *args, **options):
        self.stdout.write("Seeding support portal data...")

        users = [
            {"username": "owner_admin", "email": "owner@example.com", "password": "Owner@123", "role": SupportProfile.ROLE_OWNER},
            {"username": "manager_jane", "email": "manager@example.com", "password": "Manager@123", "role": SupportProfile.ROLE_MANAGER},
            {"username": "partner_joe", "email": "partner@example.com", "password": "Partner@123", "role": SupportProfile.ROLE_PARTNER},
            {"username": "engineer_ann", "email": "engineer@example.com", "password": "Engineer@123", "role": SupportProfile.ROLE_ENGINEER},
            {"username": "engineer_tom", "email": "engineer2@example.com", "password": "Engineer@123", "role": SupportProfile.ROLE_ENGINEER},
        ]

        created_users = {}
        for entry in users:
            user, created = User.objects.get_or_create(username=entry["username"], defaults={
                "email": entry["email"],
            })
            if created:
                user.set_password(entry["password"])
                user.save()
                self.stdout.write(f"Created user: {entry['username']}")
            else:
                self.stdout.write(f"Found user: {entry['username']}")

            profile, _ = SupportProfile.objects.get_or_create(user=user, defaults={"role": entry["role"]})
            profile.role = entry["role"]
            profile.save()
            created_users[entry["username"]] = user

        complaints = [
            {
                "title": "Partner portal login issue",
                "description": "Partner cannot sign in to the support portal and receives an unexpected error.",
                "creator": created_users["partner_joe"],
                "assigned_to": created_users["engineer_ann"],
                "manager": created_users["manager_jane"],
                "status": Complaint.STATUS_IN_PROGRESS,
            },
            {
                "title": "API response data mismatch",
                "description": "Complaint data returned by the API is missing critical fields for partner dashboards.",
                "creator": created_users["partner_joe"],
                "assigned_to": created_users["engineer_tom"],
                "manager": created_users["manager_jane"],
                "status": Complaint.STATUS_OPEN,
            },
            {
                "title": "Support engineer access request",
                "description": "Engineer Ann needs elevated permissions to update partner complaint statuses.",
                "creator": created_users["manager_jane"],
                "assigned_to": created_users["engineer_ann"],
                "manager": created_users["manager_jane"],
                "status": Complaint.STATUS_NEW,
            },
        ]

        for entry in complaints:
            complaint, created = Complaint.objects.get_or_create(
                title=entry["title"],
                defaults={
                    "description": entry["description"],
                    "creator": entry["creator"],
                    "assigned_to": entry["assigned_to"],
                    "manager": entry["manager"],
                    "status": entry["status"],
                },
            )
            if created:
                self.stdout.write(f"Created complaint: {entry['title']}")
            else:
                self.stdout.write(f"Found complaint: {entry['title']}")

        comments = [
            {
                "complaint": Complaint.objects.get(title="Partner portal login issue"),
                "author": created_users["engineer_ann"],
                "text": "I am investigating the login flow now and I will update shortly.",
            },
            {
                "complaint": Complaint.objects.get(title="API response data mismatch"),
                "author": created_users["engineer_tom"],
                "text": "I see the missing fields in v2. We should adjust the serializer.",
            },
            {
                "complaint": Complaint.objects.get(title="Support engineer access request"),
                "author": created_users["manager_jane"],
                "text": "Please confirm which permissions you require, and I will approve them.",
            },
        ]

        for entry in comments:
            comment, created = ComplaintComment.objects.get_or_create(
                complaint=entry["complaint"],
                author=entry["author"],
                text=entry["text"],
            )
            if created:
                self.stdout.write(f"Created comment for: {entry['complaint'].title}")
            else:
                self.stdout.write(f"Found comment for: {entry['complaint'].title}")

        self.stdout.write(self.style.SUCCESS("Support portal dummy data seeded."))
