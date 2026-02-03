import json
from django.core.management.base import BaseCommand
from teachers.models import Teacher
from django.utils.timezone import localtime


class Command(BaseCommand):
    help = 'Export teacher data to JSON'

    def handle(self, *args, **kwargs):
        teachers = Teacher.objects.all().prefetch_related('subject_specialization', 'assigned_class')
        data = []

        for teacher in teachers:
            data.append({
                'full_name': teacher.full_name,
                'gender': teacher.gender,
                'phone': teacher.phone,
                'email': teacher.email,
                'subject_specialization': [subject.name for subject in teacher.subject_specialization.all()],
                'assigned_class': teacher.assigned_class.name if teacher.assigned_class else None,
                'role': teacher.role,
                'created_at': localtime(teacher.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            })

        with open('teachers_export.json', 'w') as f:
            json.dump(data, f, indent=2)

        self.stdout.write(self.style.SUCCESS("✅ Exported teacher data to teachers_export.json"))
