from django.db import models
from django.utils import timezone

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('transferred', 'Transferred'),
        ('completed', 'Completed'),
    ]

    admission_number = models.CharField(max_length=20, unique=True, blank=True)
    necta_number = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Required for Form II, Form III, and Form IV only"
    )

    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    dob = models.DateField()

    form = models.IntegerField(choices=[
        (1, 'Form I'),
        (2, 'Form II'),
        (3, 'Form III'),
        (4, 'Form IV'),
    ])
    stream = models.CharField(max_length=5)

    parent_name = models.CharField(max_length=255)
    parent_contact = models.CharField(max_length=15)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.admission_number:
            current_year = timezone.now().year
            count = Student.objects.filter(created_at__year=current_year).count() + 1
            self.admission_number = f"PAR/{current_year}/{count:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.admission_number})"

    # Add first_name and last_name properties
    @property
    def first_name(self):
        return self.full_name.split()[0] if self.full_name else ''

    @property
    def last_name(self):
        parts = self.full_name.split()
        return parts[-1] if len(parts) > 1 else ''
