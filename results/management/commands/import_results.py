import json
import os
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction, close_old_connections, connections

from results.models import ExamResult, SubjectAssignment, ExamSession
from students.models import Student
from teachers.models import Teacher, Subject

SUBJECT_MAP = {
    "HIST/MAADILI": "History",
    "HIST": "History",
    "MAADILI": "Civics",
    "CIV": "Civics",
    "CHEM": "Chemistry",
    "BIO": "Biology",
    "PHY": "Physics",
}

CHECKPOINT_FILE = "import_checkpoint.txt"

class Command(BaseCommand):
    help = "Professional safe import with resume support"

    def add_arguments(self, parser):
        parser.add_argument("--input", type=str, required=True)

    def handle(self, *args, **options):
        # Force short-lived connections
        connections['default'].close()
        connections['default'].settings_dict['CONN_MAX_AGE'] = 0

        with open(options["input"], encoding="utf-8") as f:
            data = json.load(f)

        # Load last checkpoint
        start_index = 0
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, "r") as cf:
                start_index = int(cf.read().strip())

        session_cache = {}
        students_created = 0
        results_imported = 0
        skipped = 0

        for index, item in enumerate(data[start_index:], start=start_index + 1):
            try:
                close_old_connections()

                with transaction.atomic():
                    # SUBJECT
                    subject_name = SUBJECT_MAP.get(
                        item.get("subject", "").strip(),
                        item.get("subject", "").strip()
                    )
                    subject = Subject.objects.filter(name__iexact=subject_name).first()
                    if not subject:
                        skipped += 1
                        continue

                    # STUDENT
                    student = Student.objects.filter(
                        full_name=item.get("student_name", "").strip()
                    ).first()
                    if not student:
                        student = Student.objects.create(
                            full_name=item.get("student_name", "").strip(),
                            gender=item.get("gender", "M"),
                            dob=date(2008, 1, 1),
                            form=item.get("form", "1"),
                            stream=item.get("stream", "A"),
                            parent_name=item.get("parent_name", "UNKNOWN"),
                            parent_contact=item.get("parent_contact", "0000000000"),
                            status="active",
                        )
                        students_created += 1

                    # TEACHER
                    teacher, _ = Teacher.objects.get_or_create(
                        full_name=item.get("teacher_name", "").strip()
                    )

                    # EXAM SESSION
                    key = (
                        item.get("form"),
                        item.get("stream"),
                        item.get("term"),
                        item.get("year"),
                    )
                    if key not in session_cache:
                        session_cache[key], _ = ExamSession.objects.get_or_create(
                            form=item.get("form"),
                            stream=item.get("stream"),
                            term=item.get("term"),
                            year=item.get("year"),
                        )
                    exam_session = session_cache[key]

                    # SUBJECT ASSIGNMENT
                    assignment, _ = SubjectAssignment.objects.get_or_create(
                        exam_session=exam_session,
                        subject=subject,
                        teacher=teacher,
                        defaults={
                            "upload_deadline": date.today(),
                            "is_uploaded": True,
                        },
                    )

                    # EXAM RESULT
                    ExamResult.objects.update_or_create(
                        student=student,
                        assignment=assignment,
                        defaults={"score": item.get("score")},
                    )

                results_imported += 1

                # Save checkpoint
                with open(CHECKPOINT_FILE, "w") as cf:
                    cf.write(str(index))

                # Progress log
                if index % 50 == 0:
                    self.stdout.write(f"✔ Processed {index} records")

            except Exception as e:
                skipped += 1
                self.stderr.write(f"⚠ Skipped record {index}: {e}")

        self.stdout.write(self.style.SUCCESS("\n✅ IMPORT COMPLETED"))
        self.stdout.write(self.style.SUCCESS(f"👨‍🎓 Students created: {students_created}"))
        self.stdout.write(self.style.SUCCESS(f"📊 Results imported: {results_imported}"))
        self.stdout.write(self.style.WARNING(f"⚠ Skipped records: {skipped}"))

        # Remove checkpoint when done
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
