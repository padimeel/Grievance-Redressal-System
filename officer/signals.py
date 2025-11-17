from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import OfficerProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_officer_profile(sender, instance, created, **kwargs):
    if created and getattr(instance, "role", None) == "officer":
        OfficerProfile.objects.create(user=instance)
