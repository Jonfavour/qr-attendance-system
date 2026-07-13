import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model. A single table serves both students and lecturers,
    distinguished by the `role` field. This keeps Django's built-in auth
    system (login, permissions, admin) while matching the ER diagram's
    STUDENTS / LECTURERS entities.
    """
    STUDENT = 'STUDENT'
    LECTURER = 'LECTURER'
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (LECTURER, 'Lecturer'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    matric_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    staff_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=10, blank=True)  # e.g. "400" — students only

    def is_student(self):
        return self.role == self.STUDENT

    def is_lecturer(self):
        return self.role == self.LECTURER

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses',
        limit_choices_to={'role': User.LECTURER},
    )
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.course_code} - {self.title}"


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': User.STUDENT},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    academic_session = models.CharField(max_length=20, default='2025/2026')

    class Meta:
        unique_together = ('student', 'course', 'academic_session')

    def __str__(self):
        return f"{self.student} -> {self.course}"


class Session(models.Model):
    """A single class meeting for which a QR code is generated."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    qr_token = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)
    venue = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.qr_token:
            self.qr_token = secrets.token_urlsafe(24)
        if not self.expires_at:
            lifetime = getattr(settings, 'QR_SESSION_LIFETIME_SECONDS', 600)
            self.expires_at = timezone.now() + timedelta(seconds=lifetime)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.course.course_code} @ {self.created_at:%Y-%m-%d %H:%M}"


class Attendance(models.Model):
    PRESENT = 'PRESENT'
    LATE = 'LATE'
    STATUS_CHOICES = [
        (PRESENT, 'Present'),
        (LATE, 'Late'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        limit_choices_to={'role': User.STUDENT},
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_records')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PRESENT)
    gps_coordinates = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('student', 'session')  # prevents duplicate scans

    def __str__(self):
        return f"{self.student} - {self.session} - {self.status}"
