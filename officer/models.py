# backend/officer/models.py
from django.db import models
from django.conf import settings

class OfficerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='officer_profile'   # unique reverse name
    )
    department = models.CharField(max_length=128, blank=True, null=True)
    designation = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"OfficerProfile: {self.user.username} ({self.department})"


