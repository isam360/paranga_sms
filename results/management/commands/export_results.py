import json
from django.core.management.base import BaseCommand
from results.models import ExamResult
from students.models import Student
from teachers.models import Teacher
from teachers.models import Subject

class Command(BaseCommand):
    help = 'Export all exam results to a JSON file.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='exam_results.json',
            help='Output JSON file path'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        data = []

        results = ExamResult.objects.select_related(
            'student',
            'assignment__subject',
            'assignment__exam_session',
            'assignment__teacher'
        )

        for result in results:
            data.append({
                "student_uuid": str(result.student.uuid) if hasattr(result.student, 'uuid') else result.student.id,
                "student_name": result.student.full_name,
                "form": result.assignment.exam_session.form,
                "stream": result.assignment.exam_session.stream,
                "term": result.assignment.exam_session.term,
                "year": result.assignment.exam_session.year,
                "subject": result.assignment.subject.name,
                "teacher_uuid": str(result.assignment.teacher.uuid) if hasattr(result.assignment.teacher, 'uuid') else result.assignment.teacher.id,
                "teacher_name": result.assignment.teacher.full_name,
                "score": result.score
            })

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)

        self.stdout.write(self.style.SUCCESS(f'Export complete! ✅ File saved to {output_file}'))
