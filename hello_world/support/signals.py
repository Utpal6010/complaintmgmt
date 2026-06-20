from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from hello_world.support.models import SupportProfile


@receiver(post_save, sender=User)
def create_support_profile(sender, instance, created, **kwargs):
    if created:
        SupportProfile.objects.get_or_create(user=instance, defaults={"role": SupportProfile.ROLE_PARTNER})
