from django.db import models
from students.models import Student
from teachers.models import Teacher
from teachers.models import Subject
import uuid

# -----------------------------
# Exam Session
# -----------------------------
class ExamSession(models.Model):
    FORM_CHOICES = [
        (1, 'Form I'),
        (2, 'Form II'),
        (3, 'Form III'),
        (4, 'Form IV'),
    ]

    TERM_CHOICES = [
        ("Mid Term", "Mid Term"),
        ("Terminal", "Terminal"),
        ("Annual", "Annual"),
        ("Monthly Test", "Monthly Test"),
        ("Proficiency Test", "Proficiency Test"),
    ]

    form = models.IntegerField(choices=FORM_CHOICES)
    stream = models.CharField(max_length=20, blank=True, null=True)
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    year = models.PositiveIntegerField()
    is_locked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("form", "stream", "term", "year")

    def __str__(self):
        return f"{self.get_form_display()} {self.stream or ''} - {self.term} {self.year}"


# -----------------------------
# Subject Assignment
# -----------------------------
class SubjectAssignment(models.Model):
    exam_session = models.ForeignKey(ExamSession, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    upload_deadline = models.DateField()
    is_uploaded = models.BooleanField(default=False)

    # ✅ FIX: use UUIDField instead of CharField
    upload_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return f"{self.subject.name} - {self.exam_session} ({self.teacher.full_name})"


# -----------------------------
# Exam Result
# -----------------------------
class ExamResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    assignment = models.ForeignKey(SubjectAssignment, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ("student", "assignment")

    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.subject.name}: {self.score}"
