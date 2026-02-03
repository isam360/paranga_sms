from django.db import models
from django.core.exceptions import ValidationError
from students.models import Student
from cloudinary.models import CloudinaryField
import cloudinary.uploader
from django.core.files.base import ContentFile
from io import BytesIO
import pikepdf
from openpyxl import load_workbook

# ---------------- Helper functions ----------------
def optimize_pdf(file):
    try:
        output = BytesIO()
        pdf = pikepdf.open(file)
        pdf.save(output, optimize_streams=True, compress_streams=True)
        pdf.close()
        return ContentFile(output.getvalue(), name=file.name)
    except Exception as e:
        print(f"❌ PDF optimization failed: {e}")
        return file

def optimize_excel(file):
    try:
        wb = load_workbook(filename=file)
        output = BytesIO()
        wb.save(output)
        wb.close()
        return ContentFile(output.getvalue(), name=file.name)
    except Exception as e:
        print(f"❌ Excel optimization failed: {e}")
        return file

# ---------------- Announcement ----------------
class Announcement(models.Model):
    TARGET_CHOICES = [
        ('teachers', 'Teachers'),
        ('parents', 'Parents'),
        ('all', 'Everyone'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    target_group = models.CharField(max_length=20, choices=TARGET_CHOICES)
    is_correction = models.BooleanField(default=False)

    attachment = CloudinaryField(
        resource_type='raw',
        blank=True,
        null=True,
        help_text="PDF or Excel only"
    )

    # Prevent duplicate SMS
    sms_sent = models.BooleanField(default=False, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    # ---------------- Validation ----------------
    def clean(self):
        # Validate file type if a file is uploaded during this save
        try:
            filename = self.attachment.name.lower()
            if filename and not filename.endswith(('.pdf', '.xlsx')):
                raise ValidationError("Only PDF and XLSX files are allowed.")
        except Exception:
            pass  # no file uploaded yet, safe

    # ---------------- Save ----------------
    def save(self, *args, **kwargs):
        # Optimize file if it exists locally during upload
        try:
            filename = self.attachment.name.lower()
            if filename.endswith('.pdf'):
                self.attachment.file = optimize_pdf(self.attachment.file)
            elif filename.endswith('.xlsx'):
                self.attachment.file = optimize_excel(self.attachment.file)
        except Exception:
            pass  # CloudinaryResource, skip optimization

        super().save(*args, **kwargs)

    # ---------------- Delete ----------------
    def delete(self, *args, **kwargs):
        if self.attachment:
            try:
                cloudinary.uploader.destroy(
                    self.attachment.public_id,
                    resource_type='raw'
                )
            except Exception as e:
                print(f"❌ Cloudinary delete failed: {e}")
        super().delete(*args, **kwargs)

# ---------------- DisciplinaryMessage ----------------
class DisciplinaryMessage(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Disciplinary for {self.student.full_name} ({self.created_at.date()})"
