from django.contrib import admin, messages
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.conf import settings
from django.urls import reverse
from io import BytesIO
import pandas as pd
from datetime import date
from PIL import Image
import numpy as np

from .models import ExamSession, SubjectAssignment, ExamResult
from students.models import Student
from teachers.models import Subject
from .utils import get_grade_and_remark, score_to_necta_point, get_division_from_total_points

from .sms_utils import send_student_sms 


from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import datetime
from django.http import HttpResponse
import logging
from datetime import datetime

from django.contrib import admin, messages
from django.http import HttpResponse
from django.conf import settings

# PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

# Utilities
from io import BytesIO
from zipfile import ZipFile
import pandas as pd

# Models
from .models import ExamResult, ExamSession, SubjectAssignment
from students.models import Student
from teachers.models import Subject


# Utility functions
def get_necta_grade(score):
    if score is None:
        return "-"
    if score >= 75: return "A"
    if score >= 65: return "B"
    if score >= 45: return "C"
    if score >= 30: return "D"
    if score >= 20: return "E"
    return "F"

def necta_points(score):
    if score is None:
        return 0
    if score >= 75: return 1
    if score >= 65: return 2
    if score >= 45: return 3
    if score >= 30: return 4
    return 5  # F

def get_division(total_points):
    if total_points <= 17: return "I"
    if total_points <= 21: return "II"
    if total_points <= 25: return "III"
    if total_points <= 33: return "IV"
    return "0"






# -------------------- ExamSession Admin --------------------
@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ("form", "stream", "term", "year", "is_locked")
    actions = ["lock_exam_sessions"]

    @admin.action(description="🔒 Lock Selected Exam Sessions")
    def lock_exam_sessions(self, request, queryset):
        updated = queryset.update(is_locked=True)
        self.message_user(
            request,
            f"Selected exam sessions have been locked. Total: {updated}",
            level=messages.SUCCESS
        )

# -------------------- SubjectAssignment Admin --------------------
@admin.register(SubjectAssignment)
class SubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ("subject", "teacher", "exam_session", "upload_deadline", "is_uploaded")
    actions = ["email_teachers"]

    @admin.action(description="📧 Send Excel Sheets & Upload Links to Teachers")
    def email_teachers(self, request, queryset):
        import pandas as pd
        from io import BytesIO
        from django.core.mail import EmailMessage
        from django.conf import settings
        from django.urls import reverse
        from django.contrib import messages

        sent_count = 0

        for assignment in queryset.select_related("teacher", "subject", "exam_session"):
            teacher = assignment.teacher
            teacher_email = getattr(teacher, "email", None)

            # 1️⃣ Check teacher email
            if not teacher_email or not teacher_email.strip():
                self.message_user(
                    request,
                    f"❌ No valid email found for teacher {teacher.full_name}.",
                    level=messages.WARNING,
                )
                continue

            # 2️⃣ Fetch students for the form/stream
            students = Student.objects.filter(
                form=assignment.exam_session.form,
                stream=assignment.exam_session.stream
            ).order_by("admission_number")

            if not students.exists():
                self.message_user(
                    request,
                    f"⚠️ No students found for {assignment.exam_session.form}-{assignment.exam_session.stream}.",
                    level=messages.WARNING,
                )
                continue

            # 3️⃣ Build Excel in memory
            data = [
                {
                    "Admission Number": s.admission_number,
                    "Full Name": str(s.full_name).strip(),
                    "Stream": str(s.stream).strip(),
                    "Gender": str(s.gender).strip(),
                    "Score": "",
                }
                for s in students
            ]

            df = pd.DataFrame(data)
            output = BytesIO()

            try:
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="Scores")
                    workbook = writer.book
                    worksheet = writer.sheets["Scores"]

                    title_format = workbook.add_format({'bold': True, 'font_size': 14})
                    worksheet.write("G1", f"Subject: {assignment.subject.name}", title_format)
                    worksheet.write("G2", f"Exam: {assignment.exam_session.term} {assignment.exam_session.year}", title_format)
                    worksheet.set_column("A:E", 20)

                output.seek(0)  # Important: reset pointer

            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Failed to generate Excel for {assignment.subject.name} ({assignment.exam_session.form}-{assignment.exam_session.stream}): {e}",
                    level=messages.ERROR,
                )
                continue

            # 4️⃣ Build email
            upload_url = f"https://parangasec.online{reverse('results:upload_results', args=[assignment.upload_token])}"
            subject = f"📘 Upload Student Scores - {assignment.subject.name} ({assignment.exam_session.term} {assignment.exam_session.year})"

            body = (
                f"Dear {teacher.full_name},\n\n"
                "Attached is your Excel sheet for entering student scores.\n\n"
                "⚠️ Please do NOT change the column headers.\n"
                "Only fill in the 'Score' column.\n\n"
                f"Subject: {assignment.subject.name}\n"
                f"Exam Session: {assignment.exam_session.term} {assignment.exam_session.year}\n\n"
                "➡️ Upload the completed Excel file using the link below:\n\n"
                f"{upload_url}\n\n"
                f"Upload Deadline: {assignment.upload_deadline.strftime('%d %B %Y')}\n\n"
                "Thank you,\nAcademic Office"
            )

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[teacher_email],
            )

            filename = f"{assignment.subject.name}_{assignment.exam_session.term}_{assignment.exam_session.year}.xlsx"
            email.attach(
                filename,
                output.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            try:
                email.send(fail_silently=False)
                sent_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Failed to send email to {teacher.full_name}: {e}",
                    level=messages.ERROR,
                )
                continue

        # ✅ Summary
        self.message_user(
            request,
            f"✔️ Successfully sent {sent_count} email(s) with Excel attachments.",
            level=messages.SUCCESS,
        )



# -------------------- ExamResult Admin --------------------
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from datetime import date
from io import BytesIO
import pandas as pd
from django.conf import settings
from PIL import Image

# -------------------- Custom Action Form --------------------
class ExportScopeForm(forms.Form):
    EXPORT_SCOPE_CHOICES = [
        ('auto', 'Auto Detect (Based on Selection)'),
        ('form_all_streams', 'Entire Form (All Streams)'),
        ('current_stream', 'Only Current Stream'),
    ]
    export_scope = forms.ChoiceField(
        choices=EXPORT_SCOPE_CHOICES,
        required=True,
        label="Export Scope",
        help_text="Select whether to export all streams for the form or just the current stream."
    )


# -------------------- Helper: NECTA Grading --------------------
def get_grade_and_remark(score):
    if score is None or pd.isna(score):
        return "–", "No Score"

    try:
        score = float(score)
    except (ValueError, TypeError):
        return "–", "Invalid"

    if score >= 75:
        return "A", "Excellent"
    elif score >= 65:
        return "B", "Very Good"
    elif score >= 45:
        return "C", "Good"
    elif score >= 30:
        return "D", "Satisfactory"
    elif score >= 20:
        return "E", "Unsatisfactory"
    else:
        return "F", "Fail"

# ---------------- NECTA GPA POINTS ----------------



# -------------------- ExamResult Admin --------------------
# -------------------- ExamResult Admin --------------------
@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("student", "assignment", "score")
    list_filter = (
        "assignment__exam_session__form",
        "assignment__exam_session__term",
        "assignment__exam_session__stream",
    )
    search_fields = (
        "student__full_name",
        "student__admission_number",
        "assignment__subject__name",
    )
    actions = ["export_full_results" ,"export_student_report_cards_pdf", "send_results_to_parents_sms",]
    
    @admin.action(description="📊 Export Professionally Formatted Results (With Divisions, Subject Performance & GPA Summary)")
    def export_full_results(self, request, queryset):
        import pandas as pd
        import numpy as np
        from io import BytesIO
        from datetime import date
        from django.http import HttpResponse
        from django.conf import settings

        if not queryset.exists():
            self.message_user(request, "No results selected.", level=messages.ERROR)
            return

        # -------------------- Helper Functions --------------------
        def get_grade_and_remark(score):
            if score >= 75: return "A", "Excellent"
            elif score >= 65: return "B", "Very Good"
            elif score >= 45: return "C", "Good"
            elif score >= 30: return "D", "Pass"
            else: return "F", "Fail"

        # GPA points mapping (different from score points)
        def get_gpa_points(score):
            if score >= 75: return 5
            elif score >= 65: return 4
            elif score >= 45: return 3
            elif score >= 30: return 2
            else: return 0

        # Score points for division calculation (NECTA)
        def get_score_points(score):
            if score >= 75: return 1
            elif score >= 65: return 2
            elif score >= 45: return 3
            elif score >= 30: return 4
            else: return 5

        # -------------------- Detect Export Scope --------------------
        exam_session = queryset.first().assignment.exam_session
        selected_form = exam_session.form
        selected_stream = exam_session.stream

        same_form_sessions = ExamSession.objects.filter(
            form=selected_form,
            term=exam_session.term,
            year=exam_session.year
        ).order_by("stream")

        if same_form_sessions.count() > 1:
            all_results = ExamResult.objects.filter(
                assignment__exam_session__in=same_form_sessions
            ).select_related("student", "assignment", "assignment__subject", "assignment__exam_session")
            students = Student.objects.filter(form=selected_form).order_by("admission_number")
            export_scope = f"Form {selected_form} (All Streams)"
        else:
            all_results = ExamResult.objects.filter(
                assignment__exam_session=exam_session
            ).select_related("student", "assignment", "assignment__subject", "assignment__exam_session")
            students = Student.objects.filter(form=selected_form, stream=selected_stream).order_by("admission_number")
            export_scope = f"Form {selected_form} {selected_stream}"

        all_subjects = sorted(
            all_results.values_list("assignment__subject__code", flat=True).distinct()
        )

        # -------------------- Build Student Result Data --------------------
        student_results = {
            s.admission_number: {"Full Name": s.full_name, "Stream": s.stream, "Gender": s.gender}
            for s in students
        }

        for result in all_results:
            subj_name = result.assignment.subject.code
            student_results[result.student.admission_number][subj_name] = result.score

        rows, missing_count = [], 0
        for student in students:
            s_data = student_results.get(student.admission_number, {})
            total, count = 0, 0
            row = {
                "Admission No": student.admission_number,
                "Full Name": student.full_name,
                "Stream": student.stream,
                "Gender": student.gender,
            }

            # ---------------- Fill Subject Scores ----------------
            for subj in all_subjects:
                score = s_data.get(subj)
                if score is None or not isinstance(score, (int, float)) or pd.isna(score):
                    row[subj] = None
                else:
                    row[subj] = score
                    total += score
                    count += 1

            if count < len(all_subjects):
                missing_count += 1

            mean = round(total / count, 2) if count else 0
            grade, remark = get_grade_and_remark(mean)
            row.update({"Total": total, "Mean": mean, "Grade": grade, "Remark": remark})

            # ---------------- NECTA Division (Best 7 Subjects) ----------------
            valid_scores = [v for k, v in s_data.items() if isinstance(v, (int, float)) and not pd.isna(v)]
            best7_scores = sorted(valid_scores, reverse=True)[:7]

            if len(valid_scores) < 7:
                row["Division"] = "N/A"
                row["Division Points"] = None
                row["Remark"] = "Insufficient Subjects"
            else:
                best7_points = [get_score_points(s) for s in best7_scores]
                total_points = sum(best7_points)
                passed_subjects = len([s for s in best7_scores if s >= 30])
                if passed_subjects < 2:
                    division = "0"
                elif total_points <= 17:
                    division = "I"
                elif total_points <= 21:
                    division = "II"
                elif total_points <= 25:
                    division = "III"
                elif total_points <= 33:
                    division = "IV"
                else:
                    division = "0"

                row["Division Points"] = total_points
                row["Division"] = division

            rows.append(row)

        # ---------------- DataFrame & Sorting --------------------
        columns = ["Admission No", "Full Name", "Stream", "Gender"] + all_subjects + [
            "Total", "Mean", "Grade", "Remark", "Division", "Division Points"
        ]

        df = pd.DataFrame(rows, columns=columns)
        if df.empty:
            self.message_user(request, "No data found for this exam session.", level=messages.WARNING)
            return

        numeric_cols = all_subjects + ["Total", "Mean", "Division Points"]
        df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)

        # ---------------- Global Sorting by Total/Mean --------------------
        df = df.sort_values(by=["Total", "Mean"], ascending=False).reset_index(drop=True)
        df.index += 1
        if "Position" not in df.columns:
            df.insert(df.columns.get_loc("Grade") + 1, "Position", df.index)

        # ---------------- Dashboard Stats --------------------
        total_students = len(df)
        avg_mean = round(df["Mean"].mean(), 2)
        highest_mean = df["Mean"].max()
        lowest_mean = df["Mean"].min()
        grade_counts = df["Grade"].value_counts().to_dict()
        gender_counts = df["Gender"].value_counts().to_dict()
        division_counts = df["Division"].value_counts().to_dict()

        # ---------------- Excel Export --------------------
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            workbook = writer.book
            sheet = workbook.add_worksheet("Results")
            writer.sheets["Results"] = sheet

            # ---------------- Formatting --------------------
            title_fmt = workbook.add_format({'bold': True, 'font_size': 18, 'align': 'center', 'font_color': 'white', 'bg_color': '#004B8D'})
            subtitle_fmt = workbook.add_format({'bold': True, 'font_size': 13, 'align': 'center', 'font_color': '#004B8D'})
            table_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#CFE2F3', 'border': 1, 'align': 'center'})
            cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})
            numeric_fmt = workbook.add_format({'border': 1, 'num_format': '0.00', 'align': 'center'})
            missing_fmt = workbook.add_format({'bg_color': '#EEEEEE', 'border': 1})
            incomplete_fmt = workbook.add_format({'bg_color': '#B0BEC5', 'border': 1, 'align': 'center', 'italic': True})
            box_title_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'align': 'center', 'border': 1})
            box_cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})

            # ---------------- Logo --------------------
            logo_path = f"{settings.BASE_DIR}/static/images/school_logo.jpg"
            try:
                from PIL import Image
                img = Image.open(logo_path)
                w, h = img.size
                scale = min(120 / h, 120 / w)
                sheet.insert_image('A1', logo_path, {'x_scale': scale, 'y_scale': scale, 'x_offset': 5, 'y_offset': 5})
            except Exception as e:
                self.message_user(request, f"⚠️ Logo not found or invalid: {e}", level=messages.WARNING)

            # ---------------- Header --------------------
            header_start = 1
            sheet.merge_range(header_start, 2, header_start, 10, "PARANGA SECONDARY SCHOOL – DODOMA, CHEMBA", title_fmt)
            sheet.merge_range(header_start + 1, 2, header_start + 1, 10, f"OFFICIAL EXAM RESULTS – {exam_session.term} {exam_session.year}", subtitle_fmt)
            sheet.merge_range(header_start + 2, 2, header_start + 2, 10, export_scope, subtitle_fmt)

            # ---------------- Dashboard Boxes --------------------
            start_dash = header_start + 4
            sheet.merge_range(start_dash, 0, start_dash, 3, "GENERAL DETAILS", box_title_fmt)
            sheet.merge_range(start_dash, 4, start_dash, 6, "SUMMARY STATS", box_title_fmt)
            sheet.merge_range(start_dash, 7, start_dash, 9, "DIVISION PERFORMANCE", box_title_fmt)
            sheet.merge_range(start_dash, 10, start_dash, 12, "GENDER & MISSING", box_title_fmt)

            dash_row = start_dash + 1
            general_details = [
                ["School Name", "Paranga Secondary School – Dodoma, Chemba"],
                ["Exam Session", f"{exam_session.term} {exam_session.year}"],
                ["Export Scope", export_scope],
                ["Date Exported", date.today().strftime("%d %B %Y")]
            ]
            for i, (d, v) in enumerate(general_details):
                sheet.write(dash_row + i, 0, d, box_cell_fmt)
                sheet.write(dash_row + i, 1, v, box_cell_fmt)

            summary_stats = [
                ["Total Students", total_students],
                ["Average Mean", avg_mean],
                ["Highest Mean", highest_mean],
                ["Lowest Mean", lowest_mean],
            ]
            for i, (m, v) in enumerate(summary_stats):
                sheet.write(dash_row + i, 4, m, box_cell_fmt)
                sheet.write(dash_row + i, 5, v, box_cell_fmt)

            for i, (div, n) in enumerate(sorted(division_counts.items())):
                sheet.write(dash_row + i, 7, div, box_cell_fmt)
                sheet.write(dash_row + i, 8, n, box_cell_fmt)

            for i, (g, n) in enumerate(gender_counts.items()):
                sheet.write(dash_row + i, 10, g, box_cell_fmt)
                sheet.write(dash_row + i, 11, n, box_cell_fmt)
            sheet.write(dash_row + len(gender_counts), 10, "Missing Results", box_cell_fmt)
            sheet.write(dash_row + len(gender_counts), 11, missing_count, box_cell_fmt)

            # ---------------- Subject-wise Performance (Left) --------------------
            subject_summary_start = dash_row + max(len(general_details), len(summary_stats), len(division_counts), len(gender_counts)) + 2
            summary_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center'})
            summary_cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})

            subject_summary = []
            for subj in all_subjects:
                subj_scores = df[subj].dropna()
                subj_total = len(subj_scores)
                a_count = sum(subj_scores >= 75)
                b_count = sum((subj_scores >= 65) & (subj_scores < 75))
                c_count = sum((subj_scores >= 45) & (subj_scores < 65))
                d_count = sum((subj_scores >= 30) & (subj_scores < 45))
                f_count = sum(subj_scores < 30)
                subject_summary.append([subj, subj_total, a_count, b_count, c_count, d_count, f_count])

            summary_cols = ["Subject", "Total Students", "A (75-100)", "B (65-74)", "C (45-64)", "D (30-44)", "F (<30)"]
            for col_num, col_name in enumerate(summary_cols):
                sheet.write(subject_summary_start, col_num, col_name, summary_header_fmt)

            for r, row_data in enumerate(subject_summary, start=subject_summary_start + 1):
                for c, val in enumerate(row_data):
                    sheet.write(r, c, val, summary_cell_fmt)

            # ---------------- GPA Summary (Right) --------------------
            # ---------------- GPA Summary (Right) --------------------
            gpa_table_start_col = len(summary_cols) + 2
            subject_gpa_rows = []

            for subj in all_subjects:
                subj_scores = df[subj].dropna()
                if subj_scores.empty:
                    avg_points = None
                else:
                    points = [score_to_necta_point(s) for s in subj_scores]
                    avg_points = round(sum(points) / len(points), 2)

                subject_gpa_rows.append([subj, avg_points, len(subj_scores)])

            gpa_summary_cols = ["Subject", "Average NECTA Points", "Total Students"]
            for col_num, col_name in enumerate(gpa_summary_cols):
                sheet.write(subject_summary_start, gpa_table_start_col + col_num, col_name, summary_header_fmt)

            for r, row_data in enumerate(subject_gpa_rows, start=subject_summary_start + 1):
                for c, val in enumerate(row_data):
                    sheet.write(r, gpa_table_start_col + c, val, summary_cell_fmt)


            # ---------------- Conditional Coloring for GPA --------------------
            for r, row_data in enumerate(subject_gpa_rows, start=subject_summary_start + 1):
                gpa_val = row_data[1]
                if gpa_val is not None:
                    if gpa_val >= 4.5:  # High GPA
                        color_fmt = workbook.add_format({'bg_color': '#4CAF50', 'border': 1, 'align': 'center'})
                    elif gpa_val >= 3.0:  # Medium GPA
                        color_fmt = workbook.add_format({'bg_color': '#FFEB3B', 'border': 1, 'align': 'center'})
                    else:  # Low GPA
                        color_fmt = workbook.add_format({'bg_color': '#F44336', 'border': 1, 'align': 'center'})
                    # Apply formatting to the Average GPA Points cell only
                    sheet.write(r, gpa_table_start_col + 1, gpa_val, color_fmt)

            # ---------------- Overall School GPA and Comment --------------------
            # ---------------- Overall School GPA and Comment (Corrected) --------------------
            all_student_points = []

            for student in students:
                # Get all results for this student in this exam session
                student_results_qs = all_results.filter(student=student)
                student_points = []

                for res in student_results_qs:
                    if res.score is not None:
                        student_points.append(score_to_necta_point(res.score))

                if student_points:
                    # Average points for this student
                    avg_student_points = sum(student_points) / len(student_points)
                    all_student_points.append(avg_student_points)

            # Compute overall school GPA as mean of individual student GPAs
            if all_student_points:
                school_gpa = round(np.nanmean(all_student_points), 2)
            else:
                school_gpa = 0

            # Add comment based on benchmark
            benchmark_gpa = 3.5
            if school_gpa > benchmark_gpa:
                gpa_comment = f"School GPA ({school_gpa}) is ABOVE benchmark ({benchmark_gpa}) – Excellent"
            elif school_gpa < benchmark_gpa:
                gpa_comment = f"School GPA ({school_gpa}) is BELOW benchmark ({benchmark_gpa}) – Needs Improvement"
            else:
                gpa_comment = f"School GPA ({school_gpa}) is equal to benchmark ({benchmark_gpa})"

            # Write comment in Excel
            sheet.merge_range(
                subject_summary_start + len(subject_gpa_rows) + 2,
                gpa_table_start_col,
                subject_summary_start + len(subject_gpa_rows) + 2,
                gpa_table_start_col + 2,
                gpa_comment,
                box_title_fmt
            )



            # ---------------- Results Table --------------------
            start_table = subject_summary_start + max(len(subject_summary), len(subject_gpa_rows)) + 4
            for col_num, col_name in enumerate(df.columns):
                sheet.write(start_table, col_num, col_name, table_header_fmt)

            for r, (_, row_data) in enumerate(df.iterrows(), start=start_table + 1):
                for c, col_name in enumerate(df.columns):
                    val = row_data[col_name]
                    if pd.isna(val):
                        fmt = missing_fmt if col_name in all_subjects else cell_fmt
                        val = None
                    else:
                        fmt = numeric_fmt if isinstance(val, (int, float)) else cell_fmt
                    sheet.write(r, c, val, fmt)

            # Conditional formatting for failing subjects
            for col_num, subj in enumerate(all_subjects, start=4):
                sheet.conditional_format(start_table + 1, col_num, start_table + len(df), col_num, {
                    'type': 'cell', 'criteria': '<', 'value': 40,
                    'format': workbook.add_format({'bg_color': '#FF9999', 'border': 1})
                })

            # Division coloring
            division_col_idx = df.columns.get_loc("Division")
            division_colors = {'I': '#4CAF50', 'II': '#2196F3', 'III': '#FFEB3B', 'IV': '#FF9800', '0': '#F44336'}
            for r in range(len(df)):
                div_val = df.iloc[r]['Division']
                row_excel = start_table + 1 + r
                if div_val == "N/A":
                    sheet.write(row_excel, division_col_idx, div_val, incomplete_fmt)
                elif div_val in division_colors:
                    sheet.write(row_excel, division_col_idx, div_val,
                                workbook.add_format({'bg_color': division_colors[div_val], 'border': 1, 'align': 'center'}))

            # ---------------- Footer --------------------
            sheet.set_column("A:A", 14)
            sheet.set_column("B:B", 25)
            sheet.set_column("C:D", 12)
            sheet.set_column("E:Z", 11)
            footer_row = start_table + len(df) + 2
            sheet.merge_range(
                footer_row, 0, footer_row, 10,
                f"Document generated automatically on {date.today():%d %B %Y} by the Examination Management System.",
                workbook.add_format({'italic': True, 'align': 'center', 'font_color': '#666666'}),
            )

        output.seek(0)
        filename = f"Full_Results_{export_scope.replace(' ', '_')}_{exam_session.term}_{exam_session.year}.xlsx"
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response



    # -----------------------------------------------------------
    # PROFESSIONAL SMS ACTION FOR PARENTS (Student model with parent_name & parent_contact)
    # -----------------------------------------------------------
    @admin.action(description="📲 Send Results to Parents via SMS")
    def send_results_to_parents_sms(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Please select at least one result.", level=messages.ERROR)
            return

        exam_session = queryset.first().assignment.exam_session
        success = 0
        failed = 0

        # Logger setup
        logger = logging.getLogger('django')

        # Simulate Django GET request log at start
        logger.info(f'[{datetime.now():%d/%b/%Y %H:%M:%S}] "GET {request.path}?q=&o=-1 HTTP/1.1" 200 0')

        logger.info(f"[{datetime.now():%d/%b/%Y %H:%M:%S}] Starting SMS sending for {queryset.count()} student(s) in {exam_session.term} {exam_session.year}")

        for result in queryset:
            student = result.student
            parent_phone = student.parent_contact

            if not parent_phone:
                failed += 1
                logger.warning(f"[{datetime.now():%d/%b/%Y %H:%M:%S}] WARNING: Parent contact missing for {student.full_name} (Admission: {student.admission_number})")
                continue

            try:
                if send_student_sms(student, exam_session):
                    success += 1
                    logger.info(f"[{datetime.now():%d/%b/%Y %H:%M:%S}] SUCCESS: SMS sent to {student.parent_name} (Student: {student.full_name}, Admission: {student.admission_number})")
                else:
                    failed += 1
                    logger.warning(f"[{datetime.now():%d/%b/%Y %H:%M:%S}] FAILED: SMS NOT sent to {student.parent_name} (Student: {student.full_name}, Admission: {student.admission_number})")
            except Exception as e:
                failed += 1
                logger.error(f"[{datetime.now():%d/%b/%Y %H:%M:%S}] ERROR sending SMS to {student.parent_name} (Student: {student.full_name}, Admission: {student.admission_number}) | Exception: {e}")

        # Summary logs
        logger.info(f"[{datetime.now():%d/%b/%Y %H:%M:%S}] SMS sending complete. Success: {success}, Failed: {failed}")

        # Simulate Django POST request log at end
        logger.info(f'[{datetime.now():%d/%b/%Y %H:%M:%S}] "POST {request.path}?q=&o=-1 HTTP/1.1" 302 0')

        # Admin feedback
        self.message_user(
            request,
            f"SMS sending complete. ✅ Success: {success} | ⚠️ Failed: {failed}",
            level=messages.SUCCESS
        )






        
    @admin.action(description="📝 Download Official Student Reports (PDF)")
    def export_student_report_cards_pdf(modeladmin, request, queryset):

        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        import datetime

        if not queryset.exists():
            modeladmin.message_user(request, "Hakuna matokeo yaliyotolewa.", level=messages.ERROR)
            return

        exam_session = queryset.first().assignment.exam_session
        form = exam_session.form
        stream = exam_session.stream

        # ----------------------------------------
        # WANAFUNZI
        # ----------------------------------------
        students = Student.objects.filter(
            form=form, stream=stream
        ).order_by("admission_number")

        # ----------------------------------------
        # MASOMO
        # ----------------------------------------
        subjects = Subject.objects.filter(
            id__in=SubjectAssignment.objects.filter(
                exam_session__form=form,
                exam_session__stream=stream
            ).values_list('subject_id', flat=True)
        ).order_by("name")

        # ----------------------------------------
        # NECTA GRADING SYSTEM
        # ----------------------------------------
        def get_necta_grade(score):
            if score is None: return "-"
            if score >= 75: return "A"
            if score >= 65: return "B"
            if score >= 45: return "C"
            if score >= 30: return "D"
            return "F"

        def necta_points(score):
            if score is None: return 0
            if score >= 75: return 1
            if score >= 65: return 2
            if score >= 45: return 3
            if score >= 30: return 4
            return 5

        def get_division(total_points):
            if total_points <= 17: return "Daraja I"
            elif total_points <= 21: return "Daraja II"
            elif total_points <= 25: return "Daraja III"
            elif total_points <= 33: return "Daraja IV"
            else: return "Daraja 0"

        # ----------------------------------------
        # MAONI KWA KIWANGO CHA MTIHANI (NECTA REMARKS IN SWAHILI)
        # ----------------------------------------
        def get_remark(score):
            if score is None:
                return "-"
            if score >= 75:
                return "Vizuri Sana"
            if score >= 65:
                return "Vizuri"
            if score >= 45:
                return "Wastani"
            if score >= 30:
                return "Dhaifu"
            return "Mbaya Sana"

        # Optional: Convert terms to Swahili
        def sw_term(term):
            if term == "Mid Term":
                return "Mtihani wa Kati"
            if term == "Annual":
                return "Mtihani wa Mwisho wa Mwaka"
            return term

        # ----------------------------------------
        # COLLECT STUDENT REPORT DATA
        # ----------------------------------------
        students_data = []

        for student in students:
            results = ExamResult.objects.filter(
                student=student,
                assignment__exam_session__form=form,
                assignment__exam_session__stream=stream
            ).select_related("assignment__subject")

            student_subjects = []
            points_list = []

            for subj in subjects:

                mid = results.filter(
                    assignment__subject=subj,
                    assignment__exam_session__term="Mid Term"
                ).first()

                ann = results.filter(
                    assignment__subject=subj,
                    assignment__exam_session__term="Annual"
                ).first()

                mid_score = mid.score if mid else None
                ann_score = ann.score if ann else None

                # SIMPLE AVERAGE
                if mid_score is not None and ann_score is not None:
                    final_score = round((mid_score + ann_score) / 2, 2)
                else:
                    final_score = mid_score if mid_score is not None else ann_score

                grade = get_necta_grade(final_score)
                points = necta_points(final_score) if final_score is not None else None
                remark = get_remark(final_score)

                if points is not None:
                    points_list.append(points)

                student_subjects.append({
                    "subject": subj,
                    "mid": mid_score,
                    "annual": ann_score,
                    "final": final_score,
                    "grade": grade,
                    "points": points,
                    "remark": remark,
                })

            best_7_points = sorted(points_list)[:7]
            total_points = sum(best_7_points)

            valid_finals = [s["final"] for s in student_subjects if s["final"] is not None]
            mean = round(sum(valid_finals) / max(1, len(valid_finals)), 2)

            division = get_division(total_points)

            students_data.append({
                "student": student,
                "subjects": student_subjects,
                "total_points": total_points,
                "mean": mean,
                "division": division,
            })

        # Ranking
        students_data.sort(key=lambda x: x["mean"], reverse=True)
        for idx, s in enumerate(students_data, start=1):
            s["position"] = idx

        # ----------------------------------------
        # PDF SETUP
        # ----------------------------------------
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="Matokeo_{form}_{stream}.pdf"'
        )

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = styles["Title"]
        heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], alignment=TA_CENTER)
        normal_style = styles["Normal"]
        italic_style = ParagraphStyle("ItalicStyle", parent=styles["Italic"], alignment=TA_RIGHT)

        footer_style = ParagraphStyle(
            "FooterStyle",
            parent=styles["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey,
        )

        footer_text = """
    Simu: +255 675 438 191 | Baruapepe: parangasec@gmail.com<br/>
    <i>Karatasi hii ya matokeo ni hati rasmi ya shule. Hairuhusiwi kubadilishwa bila idhini ya uongozi wa shule.</i>
    """

        school_name = "Shule ya Sekondari Paranga – Chemba, Dodoma"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        closing_date = "_________________"
        opening_date = "_________________"

        # ----------------------------------------
        # BUILD SWAHILI REPORT PAGES
        # ----------------------------------------
        for index, sdata in enumerate(students_data):
            student = sdata["student"]

            elements.append(Paragraph(school_name, title_style))
            elements.append(Paragraph(
                f"Matokeo ya Mwanafunzi ({sw_term(exam_session.term)} {exam_session.year})",
                heading_style,
            ))
            elements.append(Paragraph(f"Imetengenezwa: {timestamp}", italic_style))
            elements.append(Spacer(1, 12))

            info = [
                ["Jina:", student.full_name],
                ["Namba ya Usajili:", student.admission_number],
                ["Kidato & Mkondo:", f"{form} - {stream}"],
                ["Muda & Mwaka:", f"{sw_term(exam_session.term)} - {exam_session.year}"],
                ["Nafasi Darasani:", sdata["position"]],
            ]

            tbl = Table(info, colWidths=[120, 250])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f8e9")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]))
            elements.append(tbl)
            elements.append(Spacer(1, 14))

            # SUBJECT TABLE
            subject_table = [["Somo", "Mid-Term", "Annual", "Wastani wa Mtihani", "Daraja", "Pointi", "Maoni"]]

            for rec in sdata["subjects"]:
                subject_table.append([
                    rec["subject"].name,
                    rec["mid"] if rec["mid"] is not None else "-",
                    rec["annual"] if rec["annual"] is not None else "-",
                    rec["final"] if rec["final"] is not None else "-",
                    rec["grade"],
                    rec["points"] if rec["points"] is not None else "-",
                    rec["remark"],
                ])

            st = Table(subject_table, colWidths=[100, 70, 50, 100, 50, 50, 90])
            st.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cfd8dc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]))
            elements.append(st)
            elements.append(Spacer(1, 12))

            elements.append(
                Paragraph(
                    f"Jumla ya Pointi (Masomo 7 Bora): {sdata['total_points']}     "
                    f"Wastani: {sdata['mean']}     Daraja: {sdata['division']}",
                    normal_style,
                )
            )
            elements.append(Spacer(1, 12))

            # TRAITS
            traits = ["Uhudhuriaji", "Nidhamu", "Uongozi", "Ushirikiano", "Uwajibikaji"]
            traits_table = [["Tabia / Ujuzi", "Maoni"]]

            for t in traits:
                traits_table.append([t, ""])

            tt = Table(traits_table, colWidths=[200, 170])
            tt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eceff1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(tt)
            elements.append(Spacer(1, 20))

            # TEACHER COMMENTS
            # elements.append(Paragraph("Maoni ya Mwalimu wa Masomo: ______________________________", normal_style))
            # elements.append(Spacer(1, 8))
            # elements.append(Paragraph("Jina la Mwalimu wa Masomo: _________________________________", normal_style))
            # elements.append(Spacer(1, 20))

            # SIGNATURE SECTION
            elements.append(
                Paragraph(
                    f"Tarehe ya Kufunga Shule: {closing_date}     Tarehe ya Kufungua Shule: {opening_date}",
                    normal_style,
                )
            )
            elements.append(Spacer(1, 20))

            elements.append(Paragraph("<b>Saini</b>", normal_style))
            elements.append(Spacer(1, 5))

            sign_table = Table([
                ["Sahihi ya Mwalimu wa Darasa:", "_________________________"],
                ["Sahihi ya Mwalimu wa Taaluma:", "________________________"],
                ["Sahihi ya Mkuu wa Shule:", "______________________"],
            ], colWidths=[180, 220])

            sign_table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))

            elements.append(sign_table)
            elements.append(Spacer(1, 40))

            elements.append(Paragraph(footer_text, footer_style))

            if index != len(students_data) - 1:
                elements.append(PageBreak())

        doc.build(elements)
        return response


