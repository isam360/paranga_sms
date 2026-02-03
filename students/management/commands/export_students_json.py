import json
from django.core.management.base import BaseCommand
from students.models import Student
from django.utils.timezone import localtime


class Command(BaseCommand):
    help = 'Export student data to JSON'

    def handle(self, *args, **kwargs):
        students = Student.objects.all()
        data = []

        for s in students:
            data.append({
                'admission_number': s.admission_number,
                'necta_number': s.necta_number,
                'full_name': s.full_name,
                'gender': s.gender,
                'dob': str(s.dob),
                'form': s.form,
                'stream': s.stream,
                'parent_name': s.parent_name,
                'parent_contact': s.parent_contact,
                'status': s.status,
                'created_at': localtime(s.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            })

        with open('students_export.json', 'w') as f:
            json.dump(data, f, indent=2)

        self.stdout.write(self.style.SUCCESS("✅ Exported student data to students_export.json"))
