# backend/citizen/models.py
from django.db import models
from django.conf import settings

# keep your existing profile model
class CitizenProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='citizen_profile'   # unique reverse name
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"CitizenProfile: {self.user.username}"


# New: Category model
class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# New: Grievance model
class Grievance(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = (
        (STATUS_NEW, 'New'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_REJECTED, 'Rejected'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='grievances',
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Category,
        related_name='grievances',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    # simple single file attachment; ensure MEDIA settings configured
    attachment = models.FileField(upload_to='grievance_attachments/', null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='assigned_grievances',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.pk} {self.title[:40]}'

class Feedback(models.Model):
    grievance = models.ForeignKey(
        Grievance,
        related_name='feedbacks',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='feedbacks',
        on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Feedback #{self.pk} for Grievance #{self.grievance_id}'

