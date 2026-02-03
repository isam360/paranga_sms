import os
import csv
import datetime
import tempfile

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle

from PIL import Image as PILImage, ImageDraw

from .models import Teacher, Subject, SchoolClass


# ✅ Export teachers as CSV
@admin.action(description="📄 Export selected teachers as CSV")
def export_teachers_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=teachers.csv'
    writer = csv.writer(response)
    writer.writerow([
        "Full Name", "Phone", "Role", "Assigned Class", "Subjects"
    ])
    for teacher in queryset:
        subjects = ", ".join([s.name for s in teacher.subject_specialization.all()])
        writer.writerow([
            teacher.full_name,
            teacher.phone,
            teacher.role,
            teacher.assigned_class.name if teacher.assigned_class else "",
            subjects
        ])
    return response


# ✅ Create circular logo
def create_circular_logo(input_path, output_path, size=(120, 120)):
    with PILImage.open(input_path).convert("RGBA") as im:
        im = im.resize(size, PILImage.Resampling.LANCZOS)
        mask = PILImage.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([(0, 0), size], fill=255)
        im.putalpha(mask)
        im.save(output_path, format="PNG")


# ✅ Add footer
def add_page_footer(canvas_obj, doc):
    footer_text = "© Paranga Secondary School"
    width, height = A4
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica-Oblique', 8)
    canvas_obj.setFillColor(colors.grey)
    canvas_obj.drawCentredString(width / 2.0, 15 * mm, footer_text)
    canvas_obj.restoreState()


# ✅ Professionally enhanced export teachers as PDF
@admin.action(description="🖨️ Export selected teachers as PDF")
def export_teachers_pdf(modeladmin, request, queryset):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    )
    import datetime
    import tempfile
    import os
    from django.conf import settings
    from .models import Teacher

    # Prepare HTTP response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=teachers_report.pdf"

    # PDF setup
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=25 * mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # --- Custom Styles ---
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    italic_style = styles["Italic"]
    normal_style = styles["Normal"]
    bold_style = styles["Heading4"]

    right_box_style = ParagraphStyle(
        name="RightBox",
        parent=styles["Normal"],
        fontSize=10,
        alignment=2,  # right-aligned
        backColor=colors.HexColor("#f2f4f7"),
        borderPadding=6,
        borderColor=colors.grey,
        borderWidth=0.3,
        spaceBefore=5,
        spaceAfter=5,
    )

    # --- Report Header ---
    school_name = "Paranga Secondary School"
    report_title = "Teachers List and Subject Coverage Overview"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # --- Logo Handling (Circular Logo) ---
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "school_logo.jpg")
    circular_logo_path = None
    try:
        if os.path.exists(logo_path):
            # Use NamedTemporaryFile with delete=False and keep the file alive until doc.build finishes
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                circular_logo_path = tmpfile.name
            # Make sure create_circular_logo saves the PNG properly to circular_logo_path
            create_circular_logo(logo_path, circular_logo_path)
            # Verify file exists before using
            if os.path.exists(circular_logo_path):
                logo = Image(circular_logo_path, width=35 * mm, height=35 * mm)
                logo.hAlign = "LEFT"
                elements.append(logo)
            else:
                elements.append(Paragraph("Error loading logo image.", italic_style))
        else:
            elements.append(Paragraph("School Logo Not Found", italic_style))
    except Exception as e:
        elements.append(Paragraph(f"Error processing logo: {str(e)}", italic_style))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"<b>{school_name}</b>", title_style))
    elements.append(Paragraph(report_title, heading_style))
    elements.append(Paragraph(f"Generated on: {timestamp}", italic_style))
    elements.append(Spacer(1, 12))

    # --- Teachers Table ---
    table_data = [["Full Name", "Phone", "Role", "Assigned Class", "Subjects"]]
    for teacher in queryset:
        subjects = ", ".join([s.name for s in teacher.subject_specialization.all()]) or "—"
        assigned_class = teacher.assigned_class.name if teacher.assigned_class else "—"
        table_data.append([
            teacher.full_name,
            teacher.phone,
            teacher.role,
            assigned_class,
            subjects,
        ])

    col_widths = [45 * mm, 30 * mm, 35 * mm, 30 * mm, 49 * mm]
    teacher_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    teacher_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3e6e8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ])
    )
    elements.append(teacher_table)
    elements.append(Spacer(1, 40))

    # --- Teacher Summary ---
    total_selected = queryset.count()
    assigned_class_count = queryset.filter(assigned_class__isnull=False).count()
    unassigned_class_count = queryset.filter(assigned_class__isnull=True).count()

    role_counts = {}
    for teacher in queryset:
        role = teacher.role or "Unspecified"
        role_counts[role] = role_counts.get(role, 0) + 1

    summary_data = [
        ["Total Teachers", str(total_selected)],
        ["With Assigned Class", str(assigned_class_count)],
        ["Without Assigned Class", str(unassigned_class_count)],
    ]
    for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
        summary_data.append([f"Role: {role}", str(count)])

    total_teachers_school = Teacher.objects.count()

    summary_table = Table(summary_data, colWidths=[80 * mm, 30 * mm])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f4f7")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
        ])
    )

    right_box = Paragraph(
        f"<b>Total Teachers in School</b><br/><br/><b>{total_teachers_school}</b>",
        right_box_style,
    )

    page_width = A4[0] - (18 * mm * 2)
    combined_summary = Table(
        [[summary_table, right_box]],
        colWidths=[110 * mm, page_width - 110 * mm],
    )
    combined_summary.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0, colors.white),
        ])
    )

    elements.append(Paragraph("Teacher Summary", bold_style))
    elements.append(combined_summary)
    elements.append(Spacer(1, 20))

    # --- NEW PAGE BREAK BEFORE SUBJECT COVERAGE OVERVIEW ---
    elements.append(PageBreak())

    # --- Subject Coverage Overview (Professional Layout) ---
    elements.append(Paragraph("Subject Coverage Overview", bold_style))
    elements.append(Spacer(1, 8))

    subject_counts = {}
    for teacher in queryset:
        for subject in teacher.subject_specialization.all():
            subject_counts[subject.name] = subject_counts.get(subject.name, 0) + 1

    if subject_counts:
        total_teachers = queryset.count() or 1
        sorted_subjects = sorted(subject_counts.items(), key=lambda x: x[0])

        coverage_data = [
            ["#", "Subject Name", "Teachers Assigned", "Coverage (%)", "Coverage Level"]
        ]

        for idx, (subject, count) in enumerate(sorted_subjects, start=1):
            coverage_percentage = (count / total_teachers) * 100
            if coverage_percentage >= 60:
                level = "Well Covered"
                color = colors.HexColor("#e8f5e9")  # light green
            elif 30 <= coverage_percentage < 60:
                level = "Moderate"
                color = colors.HexColor("#fff9e6")  # light yellow
            else:
                level = "Low"
                color = colors.HexColor("#fdecea")  # light red
            coverage_data.append([
                str(idx),
                subject,
                str(count),
                f"{coverage_percentage:.1f}%",
                level,
            ])

        col_widths = [10 * mm, 60 * mm, 35 * mm, 25 * mm, 50 * mm]
        coverage_table = Table(coverage_data, colWidths=col_widths, repeatRows=1)

        coverage_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e6ed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )

        # Apply color shading based on coverage levels
        for row_index, row in enumerate(coverage_data[1:], start=1):
            level = row[4]
            if level == "Well Covered":
                bg_color = colors.HexColor("#edf7ed")
            elif level == "Moderate":
                bg_color = colors.HexColor("#fffdf0")
            else:
                bg_color = colors.HexColor("#fdf3f2")
            coverage_table.setStyle([("BACKGROUND", (0, row_index), (-1, row_index), bg_color)])

        elements.append(coverage_table)
        elements.append(Spacer(1, 10))

        avg_coverage = sum(subject_counts.values()) / len(subject_counts)
        elements.append(Paragraph(
            f"<i>Average coverage: {avg_coverage:.1f} teachers per subject.</i>",
            italic_style
        ))

        elements.append(Spacer(1, 6))
        legend_text = (
            "<b>Coverage Key:</b><br/>"
            "• Well Covered — 60% or more teachers<br/>"
            "• Moderate — 30% to 59% coverage<br/>"
            "• Low — below 30% coverage"
        )
        elements.append(Paragraph(legend_text, ParagraphStyle(
            name="LegendBox",
            parent=styles["Normal"],
            fontSize=9,
            backColor=colors.HexColor("#f9f9fb"),
            borderColor=colors.HexColor("#d3d3d3"),
            borderWidth=0.3,
            borderPadding=6,
            leading=12,
        )))
    else:
        elements.append(Paragraph("<i>No subject specialization data available.</i>", italic_style))

    # --- Build PDF ---
    doc.build(elements, onFirstPage=add_page_footer, onLaterPages=add_page_footer)

    # Clean up the temp circular logo image only AFTER PDF generation
    if circular_logo_path and os.path.exists(circular_logo_path):
        try:
            os.remove(circular_logo_path)
        except Exception:
            pass  # silently ignore errors on cleanup

    return response



# ✅ Export attendance sheet (PDF)
@admin.action(description="📝 Export attendance sheet (PDF)")
def export_attendance_sheet_pdf(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=attendance_agenda_sheet.pdf'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=30 * mm
    )

    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    italic_style = styles['Italic']

    school_name = "Paranga Secondary School"
    report_title = "Meeting Attendance & Agenda"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'school_logo.jpg')
    circular_logo_path = None
    if os.path.exists(logo_path):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            circular_logo_path = tmpfile.name
        create_circular_logo(logo_path, circular_logo_path)

        img = Image(circular_logo_path, width=40 * mm, height=40 * mm)
        img.hAlign = 'LEFT'
        elements.append(img)
    else:
        elements.append(Paragraph("School Logo Not Found", italic_style))

    elements.append(Paragraph(school_name, title_style))
    elements.append(Paragraph(report_title, heading_style))
    elements.append(Paragraph(f"Generated on: {timestamp}", italic_style))
    elements.append(Spacer(1, 12))

    attendance_data = [["Full Name", "Role", "Signature"]]
    for teacher in queryset:
        attendance_data.append([teacher.full_name, teacher.role, ""])

    att_col_widths = [70 * mm, 40 * mm, 60 * mm]
    attendance_table = Table(attendance_data, colWidths=att_col_widths)
    attendance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#eceff1")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(attendance_table)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Meeting Agenda", heading_style))
    elements.append(Spacer(1, 10))

    agenda_data = [["#", "Agenda Item", "Presenter", "Time"]]
    for i in range(1, 9):
        agenda_data.append([str(i), "", "", ""])

    agenda_col_widths = [10 * mm, 90 * mm, 40 * mm, 30 * mm]
    agenda_table = Table(agenda_data, colWidths=agenda_col_widths)
    agenda_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#eceff1")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(agenda_table)

    doc.build(elements, onFirstPage=add_page_footer, onLaterPages=add_page_footer)

    if circular_logo_path and os.path.exists(circular_logo_path):
        os.remove(circular_logo_path)

    return response


# ✅ Register TeacherAdmin
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "get_subjects", "assigned_class", "role")
    list_filter = ("role", "assigned_class")
    search_fields = ("full_name", "phone")
    actions = [
        export_teachers_csv,
        export_teachers_pdf,
        export_attendance_sheet_pdf,
    ]
    actions_on_top = True

    def get_subjects(self, obj):
        return ", ".join([s.name for s in obj.subject_specialization.all()])
    get_subjects.short_description = "Subjects"


# ✅ Register other models
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "level")
    list_filter = ("level",)
    search_fields = ("name",)
