from django.db import models
from django.conf import settings

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @staticmethod
    def preload_subjects():
        subjects = [
            {"name": "Civics", "code": "CIV"},
            {"name": "History", "code": "HIST"},
            {"name": "Geography", "code": "GEO"},
            {"name": "Kiswahili", "code": "KISW"},
            {"name": "English Language", "code": "ENG"},
            {"name": "Mathematics", "code": "MATH"},
            {"name": "Biology", "code": "BIO"},
            {"name": "Physics", "code": "PHY"},
            {"name": "Chemistry", "code": "CHEM"},
            {"name": "EDK", "code": "EDK"},
            {"name": "B/STUDIES", "code": "B/STUDIES"},
            {"name": "HIST/MAADILI", "code": "HIST/MAADILI"},
        ]
        for subj in subjects:
            Subject.objects.get_or_create(name=subj["name"], code=subj["code"])

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"


class SchoolClass(models.Model):
    LEVEL_CHOICES = [
        ('Form I', 'Form I'),
        ('Form II', 'Form II'),
        ('Form III', 'Form III'),
        ('Form IV', 'Form IV'),
    ]
    name = models.CharField(max_length=20, unique=True)  # e.g. "Form II A"
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.name


class Teacher(models.Model):
    ROLE_CHOICES = [
        ('head', 'Head Teacher'),
        ('deputy', 'Deputy Head Teacher'),
        ('academic', 'Academic Teacher'),
        ('assistant_academic', 'Assistant Academic'),
        ('discipline', 'Discipline Master'),
        ('secretary', 'Secretary'),
        ('accountant', 'Accountant'),
        ('normal', 'Normal Teacher'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)  # for sending results

    # Many-to-many subjects
    subject_specialization = models.ManyToManyField(Subject, related_name="teachers")

    # One main class (optional)
    assigned_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='normal')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

    def __str__(self):
        return self.full_name

    @property
    def first_name(self):
        return self.full_name.split()[0] if self.full_name else ''

    @property
    def last_name(self):
        parts = self.full_name.split()
        return parts[-1] if len(parts) > 1 else ''
