from django.db import models
from django.utils import timezone
from datetime import timedelta


class Complaint(models.Model):

    # -----------------------------
    # STATUS OPTIONS
    # -----------------------------
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Escalated', 'Escalated'),
        ('Resolved', 'Resolved'),   # Waiting for citizen confirmation
        ('Closed', 'Closed'),       # Final state
    ]

    # -----------------------------
    # CATEGORY OPTIONS
    # -----------------------------
    CATEGORY_CHOICES = [
        ('Infrastructure', 'Infrastructure'),
        ('Healthcare', 'Healthcare'),
        ('Water & Utilities', 'Water & Utilities'),
        ('Sanitation', 'Sanitation'),
        ('Other', 'Other'),
    ]

    # -----------------------------
    # PRIORITY OPTIONS
    # -----------------------------
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    # -----------------------------
    # CITIZEN INFORMATION
    # -----------------------------
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    area = models.CharField(max_length=100)

    # -----------------------------
    # COMPLAINT DETAILS
    # -----------------------------
    description = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Other')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # -----------------------------
    # SLA TRACKING
    # -----------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)

    # -----------------------------
    # RESOLUTION & CLOSURE
    # -----------------------------
    resolution_photo = models.ImageField(upload_to="resolutions/", null=True, blank=True)
    resolution_note = models.TextField(null=True, blank=True)

    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # -----------------------------
    # FEEDBACK SYSTEM
    # -----------------------------
    rating = models.IntegerField(blank=True, null=True)
    feedback_comment = models.TextField(blank=True, null=True)

    # -----------------------------
    # SAVE LOGIC (SLA AUTOMATION)
    # -----------------------------
    def save(self, *args, **kwargs):

        # Set deadline ONLY when creating
        if self.pk is None:

            if self.category == 'Infrastructure':
                self.deadline = timezone.now() + timedelta(days=5)

            elif self.category == 'Healthcare':
                self.deadline = timezone.now() + timedelta(days=3)

            else:
                self.deadline = timezone.now() + timedelta(days=4)

        super().save(*args, **kwargs)

    # -----------------------------
    # OVERDUE CHECK
    # -----------------------------
    def is_overdue(self):
        return (
            self.deadline is not None and
            self.status in ["Pending", "In Progress"] and
            timezone.now() > self.deadline
        )

    # -----------------------------
    # AUTO ESCALATION
    # -----------------------------
    @staticmethod
    def update_overdue_complaints():
        now = timezone.now()

        Complaint.objects.filter(
            status__in=["Pending", "In Progress"],
            deadline__isnull=False,
            deadline__lt=now
        ).update(status="Escalated")

    # -----------------------------
    # STATE TRANSITION METHODS
    # -----------------------------
    def mark_in_progress(self):
        if self.status != "Pending":
            raise ValueError("Only pending complaints can move to In Progress.")

        self.status = "In Progress"
        self.save()

    def mark_resolved(self, photo, note):
        if self.status not in ["In Progress", "Escalated"]:
            raise ValueError("Only active complaints can be resolved.")

        if not photo:
            raise ValueError("Resolution photo is required.")

        self.status = "Resolved"
        self.resolution_photo = photo
        self.resolution_note = note
        self.resolved_at = timezone.now()
        self.save()

    def reject_resolution(self):
        if self.status != "Resolved":
            raise ValueError("Only resolved complaints can be rejected.")

        self.status = "Escalated"
        self.save()

    def mark_closed(self):
        if self.status != "Resolved":
            raise ValueError("Only resolved complaints can be closed.")

        self.status = "Closed"
        self.closed_at = timezone.now()
        self.save()

    # -----------------------------
    # AUTO CLOSE AFTER 7 DAYS
    # -----------------------------
    @staticmethod
    def auto_close_resolved():
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)

        Complaint.objects.filter(
            status="Resolved",
            resolved_at__lt=seven_days_ago
        ).update(status="Closed", closed_at=now)

    # -----------------------------
    # STRING REPRESENTATION
    # -----------------------------
    def __str__(self):
        return f"{self.name} - {self.category} - {self.status}"