from django.core.management.base import BaseCommand
from teachers.models import Subject

class Command(BaseCommand):
    help = 'Preloads NECTA subjects into the database.'

    def handle(self, *args, **options):
        Subject.preload_subjects()
        self.stdout.write(self.style.SUCCESS("✅ NECTA subjects preloaded successfully."))
