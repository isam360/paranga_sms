import json
from django.core.management.base import BaseCommand
from teachers.models import Teacher, Subject, SchoolClass
from django.db import transaction


class Command(BaseCommand):
    help = 'Import teacher data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing teacher data')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to load JSON: {e}"))
            return

        for item in data:
            try:
                full_name = item['full_name']
                gender = item['gender']
                phone = item['phone']
                role = item.get('role', 'normal')
                subject_names = item.get('subject_specialization', [])
                assigned_class_name = item.get('assigned_class')

                teacher, created = Teacher.objects.get_or_create(
                    phone=phone,
                    defaults={
                        'full_name': full_name,
                        'gender': gender,
                        'role': role
                    }
                )

                if not created:
                    teacher.full_name = full_name
                    teacher.gender = gender
                    teacher.role = role
                    teacher.save()

                # Set assigned class
                if assigned_class_name:
                    try:
                        school_class = SchoolClass.objects.get(name=assigned_class_name)
                        teacher.assigned_class = school_class
                        teacher.save()
                    except SchoolClass.DoesNotExist:
                        self.stderr.write(self.style.WARNING(f"⚠️ Class '{assigned_class_name}' not found for {full_name}"))

                # Set subject specialization
                teacher.subject_specialization.clear()
                for subj_name in subject_names:
                    subject, _ = Subject.objects.get_or_create(name=subj_name)
                    teacher.subject_specialization.add(subject)

                self.stdout.write(self.style.SUCCESS(f"✅ Imported: {full_name}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error importing {item.get('full_name', 'Unknown')}: {e}"))
