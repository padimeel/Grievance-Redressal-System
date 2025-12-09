# adminpanel/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Index
from django.core.validators import MinValueValidator, MaxValueValidator

# If you prefer, you can keep `User = settings.AUTH_USER_MODEL` and use `User` in FKs.
AUTH_USER = settings.AUTH_USER_MODEL


def grievance_upload_to(instance, filename):
    """
    File upload path. If tracking_id is not yet available (during initial save),
    files will be stored under "untracked/" and can be moved/handled later if needed.
    """
    tracking = instance.tracking_id or "untracked"
    return f"grievance_files/{tracking}/{filename}"


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=150)
    department = models.ForeignKey(
        AUTH_USER,  # temporary guard if migrations expect a string; will be replaced below by Department in final code
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categories",
    )

    # NOTE: The above temporary FK was set to AUTH_USER to avoid accidental imports while editing.
    # Replace with Department below by setting attribute after class definition OR simply edit to:
    # department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="categories")

    class Meta:
        unique_together = ("name", "department")
        ordering = ["department__name", "name"]

    def __str__(self):
        if self.department:
            return f"{self.name} ({self.department.name})"
        return self.name


# Replace the placeholder FK in Category to reference Department properly.
# (We do this here to keep the file self-contained when pasted; if you edit directly,
# replace the Category.department field with Department FK as required.)
Category._meta.get_field("department").remote_field.model = Department


class Grievance(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_ESCALATED = "escalated"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_ESCALATED, "Escalated"),
    ]

    tracking_id = models.CharField(max_length=40, unique=True, db_index=True, blank=True)

    # Use settings.AUTH_USER_MODEL as string for safe migrations
    user = models.ForeignKey(
        AUTH_USER,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="adminpanel_grievances",
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="grievances",
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="grievances",
    )
    attached_file = models.FileField(upload_to=grievance_upload_to, null=True, blank=True)

    assigned_officer = models.ForeignKey(
        AUTH_USER,
        null=True,
        blank=True,
        related_name="adminpanel_assigned_grievances",
        on_delete=models.SET_NULL,
    )

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            Index(fields=["status"]),
            Index(fields=["created_at"]),
            Index(fields=["department"]),
            Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.tracking_id or 'NEW'} - {self.title}"

    def _generate_tracking_id(self):
        year = timezone.now().year
        # Use pk padded to 6 digits
        return f"KER-{year}-{self.pk:06d}"

    def save(self, *args, **kwargs):
        """
        On create: first save to obtain PK, then generate and persist a tracking_id.
        This approach avoids race-conditions with unique tracking_id generation when using the PK.
        """
        need_tracking = not bool(self.tracking_id)
        if need_tracking and not self.pk:
            # First save to get a PK
            super().save(*args, **kwargs)
            self.tracking_id = self._generate_tracking_id()
            # Use update to avoid re-running save logic and potential recursion
            Grievance.objects.filter(pk=self.pk).update(tracking_id=self.tracking_id)
            return
        super().save(*args, **kwargs)


class GrievanceRemark(models.Model):
    grievance = models.ForeignKey(Grievance, on_delete=models.CASCADE, related_name="remarks")
    officer = models.ForeignKey(
        AUTH_USER,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="adminpanel_remarks",
    )
    remark = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        who = self.officer.get_full_name() if getattr(self.officer, "get_full_name", None) else "Unknown"
        return f"Remark by {who} on {self.created_at:%Y-%m-%d %H:%M}"


class Feedback(models.Model):
    grievance = models.OneToOneField(Grievance, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-submitted_at",)

    def __str__(self):
        return f"Feedback {self.rating} for {self.grievance.tracking_id}"


class ChangeLog(models.Model):
    user = models.ForeignKey(
        AUTH_USER,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="adminpanel_changelogs",
    )
    grievance = models.ForeignKey(
        Grievance,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="changelogs",
    )
    action = models.CharField(max_length=100)
    before = models.TextField(blank=True, null=True)
    after = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        who = self.user.get_full_name() if getattr(self.user, "get_full_name", None) else "System"
        return f"{self.timestamp:%Y-%m-%d %H:%M} | {who} | {self.action}"


