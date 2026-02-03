from django.shortcuts import render
from django.db.models import Avg
from students.models import Student
from teachers.models import Teacher, Subject
from results.models import ExamSession, ExamResult
from announcements.models import Announcement
from datetime import timedelta
from django.utils import timezone

def landing_page(request):
    latest_exam = ExamSession.objects.order_by("-year", "-id").first()

    students_count = Student.objects.filter(status="active").count()
    teachers_count = Teacher.objects.count()
    subjects_count = Subject.objects.count()
    exam_sessions_count = ExamSession.objects.count()
    results_uploaded = ExamResult.objects.exclude(score__isnull=True).count()

    performance_dict = {
        f"Form {i}": ExamResult.objects.filter(student__form=i).aggregate(avg=Avg("score"))["avg"] or 0
        for i in range(1, 5)
    }

    # Convert dict to lists for Chart.js
    performance_labels = list(performance_dict.keys())
    performance_values = list(performance_dict.values())
    
    # Calculate sum of performance values
    performance_sum = sum(performance_values)
    
    # Check if we have valid performance data
    has_performance_data = (
        performance_values and 
        len(performance_values) > 0 and 
        performance_sum > 0
    )

    attachments = Announcement.objects.filter(attachment__isnull=False).order_by("-created_at")
    one_week_ago = timezone.now() - timedelta(days=7)
    active_announcements = attachments.filter(created_at__gte=one_week_ago)

    context = {
        "students_count": students_count,
        "teachers_count": teachers_count,
        "subjects_count": subjects_count,
        "exam_sessions_count": exam_sessions_count,
        "results_uploaded": results_uploaded,
        "latest_exam": latest_exam,
        "performance_labels": performance_labels,
        "performance_values": performance_values,
        "performance_sum": performance_sum,  # Add this
        "has_performance_data": has_performance_data,  # Add this
        "attachments": attachments,
        "active_announcements": active_announcements,
    }

    return render(request, "landingpage/landing.html", context)

def help_page(request):
    return render(request, "landingpage/help.html")