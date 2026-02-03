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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

from PIL import Image as PILImage, ImageDraw

from .models import Student


# ====================== EXPORT ACTIONS ======================

@admin.action(description="📄 Export selected students as CSV")
def export_students_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=students.csv'
    
    writer = csv.writer(response)
    writer.writerow([
        "Full Name", "Admission Number", "Form", "Stream", "Status",
        "Parent Name", "Parent Contact", "Gender", "Necta Number"
    ])
    for student in queryset:
        writer.writerow([
            student.full_name,
            student.admission_number,
            student.form,
            student.stream,
            student.status,
            student.parent_name,
            student.parent_contact,
            student.gender,
            student.necta_number,
        ])
    return response


# ====================== HELPER FUNCTIONS ======================

def create_circular_logo(input_path, output_path, size=(120, 120)):
    with PILImage.open(input_path).convert("RGBA") as im:
        im = im.resize(size, PILImage.Resampling.LANCZOS)
        mask = PILImage.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([(0, 0), size], fill=255)
        im.putalpha(mask)
        im.save(output_path, format="PNG")


def add_page_footer(canvas_obj, doc):
    footer_text = "© Paranga Secondary School"
    width, height = A4
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica-Oblique', 8)
    canvas_obj.setFillColor(colors.grey)
    canvas_obj.drawCentredString(width / 2.0, 15 * mm, footer_text)
    canvas_obj.restoreState()


# ====================== COMMON STYLE ======================

cell_style = ParagraphStyle(
    name="CellStyle",
    fontSize=9,
    leading=11,
    alignment=TA_LEFT,
    wordWrap="CJK",
)


# ====================== PDF EXPORT: STUDENTS ======================

from reportlab.platypus import Flowable

# ===================== Helper: BlackBox =====================
class BlackBox(Flowable):
    """A small centered black rectangle for missing NECTA numbers."""
    def __init__(self, width=20, height=7):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        # Center the rectangle inside its table cell
        x_offset = (self._width - self.width) / 2 if hasattr(self, "_width") else 0
        y_offset = (self._height - self.height) / 2 if hasattr(self, "_height") else 0
        self.canv.saveState()
        self.canv.setFillColor(colors.black)
        self.canv.rect(x_offset, y_offset, self.width, self.height, stroke=0, fill=1)
        self.canv.restoreState()


# ===================== PDF EXPORT: STUDENTS LIST =====================
@admin.action(description="🖨️ Export selected students as PDF")
def export_students_pdf(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=students.pdf'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=30 * mm
    )

    elements = []

    # ---- Styles ----
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    italic_style = styles['Italic']

    # ---- Report Header ----
    school_name = "Paranga Secondary School"
    report_title = "Students List"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---- School Logo ----
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'school_logo.jpg')
    circular_logo_path = None

    if os.path.exists(logo_path):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            circular_logo_path = tmpfile.name
        create_circular_logo(logo_path, circular_logo_path)
        img = Image(circular_logo_path, width=40 * mm, height=40 * mm)
        img.hAlign = 'LEFT'
        elements.append(img)
        elements.append(Spacer(1, 12))
    else:
        elements.append(Paragraph("School Logo Not Found", italic_style))

    # ---- Title Section ----
    elements.append(Paragraph(school_name, title_style))
    elements.append(Paragraph(report_title, heading_style))
    elements.append(Paragraph(f"Generated on: {timestamp}", italic_style))
    elements.append(Spacer(1, 12))

    # ---- Table Data ----
    data = [[
        "No", "Admission No", "Full Name", "Form", "Stream", "Status", "Gender", "NECTA No"
    ]]

    for i, student in enumerate(queryset.order_by("admission_number"), start=1):
        necta_value = (
            Paragraph(student.necta_number, styles['Normal'])
            if student.necta_number
            else BlackBox(width=18, height=7)
        )

        row = [
            Paragraph(str(i), styles['Normal']),
            Paragraph(student.admission_number, styles['Normal']),
            Paragraph(student.full_name.upper(), styles['Normal']),
            Paragraph(f"Form {student.form}", styles['Normal']),
            Paragraph(student.stream, styles['Normal']),
            Paragraph(student.status.capitalize(), styles['Normal']),
            Paragraph(dict(Student.GENDER_CHOICES).get(student.gender, ""), styles['Normal']),
            necta_value,
        ]
        data.append(row)

    # ---- Column Widths ----
    col_widths = [
        12 * mm,  # No
        28 * mm,  # Admission No
        60 * mm,  # Full Name
        18 * mm,  # Form
        15 * mm,  # Stream
        15 * mm,  # Status
        18 * mm,  # Gender
        35 * mm,  # Necta No
    ]

    # ---- Table Styling ----
    table = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=1)
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#eceff1")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        # Body cells
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),

        # Grid and alternating rows
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
    ]))

    elements.append(table)

    # ---- Footer ----
    def add_page_footer(canvas, doc):
        footer_text = "© Paranga Secondary School"
        footer_y = 15 * mm
        canvas.saveState()
        canvas.setFont('Helvetica-Oblique', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(A4[0] / 2.0, footer_y, footer_text)
        canvas.restoreState()

    # ---- Build PDF ----
    doc.build(elements, onFirstPage=add_page_footer, onLaterPages=add_page_footer)

    if circular_logo_path and os.path.exists(circular_logo_path):
        os.remove(circular_logo_path)

    return response

# ====================== PDF EXPORT: EXAM SCORE SHEET ======================
from reportlab.platypus import Flowable

# ===================== Helper: BlackBox =====================
class BlackBox(Flowable):
    """A small filled black rectangle centered in its table cell."""
    def __init__(self, width=20, height=7):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        # Calculate offsets to center the box horizontally & vertically
        x_offset = (self._width - self.width) / 2 if hasattr(self, "_width") else 0
        y_offset = (self._height - self.height) / 2 if hasattr(self, "_height") else 0
        self.canv.saveState()
        self.canv.setFillColor(colors.black)
        self.canv.rect(x_offset, y_offset, self.width, self.height, stroke=0, fill=1)
        self.canv.restoreState()


# ===================== PDF EXPORT: EXAM SCORE SHEET =====================
@admin.action(description="📝 Export Exam Score Sheet (PDF)")
def export_exam_score_sheet_pdf(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=exam_score_sheet.pdf'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=30 * mm,
    )
    elements = []

    # ---- Styles ----
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    italic_style = styles['Italic']
    normal_style = styles['Normal']

    school_name = "Paranga Secondary School"
    report_title = "Exam Attendance & Score Sheet"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---- School logo ----
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'school_logo.jpg')
    circular_logo_path = None

    if os.path.exists(logo_path):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            circular_logo_path = tmpfile.name
        create_circular_logo(logo_path, circular_logo_path)
        img = Image(circular_logo_path, width=40 * mm, height=40 * mm)
        img.hAlign = 'LEFT'
        elements.append(img)
        elements.append(Spacer(1, 12))
    else:
        elements.append(Paragraph("School Logo Not Found", italic_style))

    # ---- Report Header ----
    elements.append(Paragraph(school_name, title_style))
    elements.append(Paragraph(report_title, heading_style))
    elements.append(Paragraph(f"Generated on: {timestamp}", italic_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Exam Type: ________________", normal_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Subject: __________________", normal_style))
    elements.append(Spacer(1, 12))

    # ---- Check whether to include NECTA column ----
    include_necta = any(str(student.form) in ["2", "4"] for student in queryset)

    # ---- Table Header ----
    if include_necta:
        data = [["Admission No", "Full Name", "Form", "Stream", "NECTA No", "Score", "Signature"]]
    else:
        data = [["Admission No", "Full Name", "Form", "Stream", "Score", "Signature"]]

    # ---- Table Body ----
    for student in queryset:
        row = [
            Paragraph(student.admission_number, cell_style),
            Paragraph(student.full_name, cell_style),
            Paragraph(f"Form {student.form}", cell_style),
            Paragraph(student.stream, cell_style),
        ]

        if include_necta:
            if str(student.form) in ["2", "4"]:
                if student.necta_number:
                    row.append(Paragraph(student.necta_number, cell_style))
                else:
                    # Professional centered black rectangle
                    row.append(BlackBox(width=18, height=7))
            else:
                row.append("")  # blank for other forms

        # Add placeholders for Score and Signature
        row.extend(["", ""])
        data.append(row)

    # ---- Column Widths ----
    if include_necta:
        col_widths = [25 * mm, 55 * mm, 18 * mm, 18 * mm, 30 * mm, 20 * mm, 35 * mm]
    else:
        col_widths = [30 * mm, 55 * mm, 18 * mm, 20 * mm, 20 * mm, 35 * mm]

    # ---- Table Design ----
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header Row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#eceff1")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        # Body Rows
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),

        # Grid & Background
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
    ]))

    elements.append(table)

    # ---- Footer ----
    def add_page_footer(canvas, doc):
        footer_text = "© Paranga Secondary School"
        footer_y = 15 * mm
        canvas.saveState()
        canvas.setFont('Helvetica-Oblique', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(A4[0] / 2.0, footer_y, footer_text)
        canvas.restoreState()

    # ---- Build PDF ----
    doc.build(elements, onFirstPage=add_page_footer, onLaterPages=add_page_footer)

    if circular_logo_path and os.path.exists(circular_logo_path):
        os.remove(circular_logo_path)

    return response

# ====================== PDF EXPORT: ATTENDANCE SHEET ======================
# ====================== PDF EXPORT: ATTENDANCE SHEET ======================
@admin.action(description="📋 Export Attendance Sheet (PDF)")
def export_attendance_sheet_pdf(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=attendance_sheet.pdf'

    doc = SimpleDocTemplate(
        response, 
        pagesize=A4,
        rightMargin=20*mm, 
        leftMargin=20*mm,
        topMargin=20*mm, 
        bottomMargin=30*mm
    )

    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    # ---- Header ----
    elements.append(Paragraph("Paranga Secondary School", title_style))
    elements.append(Paragraph("Exam Attendance Sheet", heading_style))
    elements.append(Paragraph(f"Generated on: {datetime.datetime.now():%Y-%m-%d %H:%M}", normal_style))
    elements.append(Spacer(1, 12))

    # ---- Exam Type & Room ----
    elements.append(Paragraph("Exam Type: __________", normal_style))
    elements.append(Paragraph("Room Number: ________", normal_style))
    elements.append(Spacer(1, 12))

    # ---- Student Table ----
    data = [["No", "Admission No", "Full Name", "Form", "Stream", "Signature"]]
    for i, student in enumerate(queryset.order_by("admission_number"), start=1):
        data.append([
            str(i),
            student.admission_number,
            student.full_name.upper(),
            f"Form {student.form}",
            student.stream,
            "",  # Signature placeholder
        ])

    col_widths = [12*mm, 35*mm, 60*mm, 20*mm, 25*mm, 30*mm]  # Adjusted widths after removing Gender
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#eceff1")),
        ('ALIGN',(0,0),(-1,0),'CENTER'),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.whitesmoke]),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    elements.append(table)

    # ---- Footer ----
    doc.build(elements, onFirstPage=add_page_footer, onLaterPages=add_page_footer)

    return response


# ====================== DJANGO ADMIN CONFIG ======================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "full_name", "admission_number", "form", "stream",
        "status", "parent_name", "parent_contact"
    )
    list_filter = ("form", "stream", "status", "gender")
    search_fields = (
        "full_name", "admission_number", "parent_name",
        "parent_contact", "necta_number"
    )
    readonly_fields = ("admission_number", "created_at")
    date_hierarchy = "created_at"
    ordering = ("full_name",)
    actions = [
        export_students_csv,
        export_students_pdf,
        export_exam_score_sheet_pdf,
        export_attendance_sheet_pdf
    ]
    actions_on_top = True
    actions_on_bottom = False
