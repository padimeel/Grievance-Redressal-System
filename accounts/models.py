# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('officer', 'Officer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')

    def is_citizen(self):
        return self.role == 'citizen'

    def is_officer(self):
        return self.role == 'officer'

    def is_adminpanel(self):
        return self.role == 'admin'

