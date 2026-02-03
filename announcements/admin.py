from django.contrib import admin
from django.http import HttpResponse
from django.conf import settings
import os, datetime, tempfile

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from PIL import Image as PILImage, ImageDraw

from .models import Announcement, DisciplinaryMessage
from teachers.models import Teacher
from core.sms_utils import send_sms

# --------------------- HELPER FUNCTIONS ---------------------

def create_circular_logo(input_path, output_path, size=(100, 100)):
    with PILImage.open(input_path).convert("RGBA") as im:
        im = im.resize(size, PILImage.Resampling.LANCZOS)
        mask = PILImage.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([(0, 0), size], fill=255)
        im.putalpha(mask)
        im.save(output_path, format="PNG")


def swahili_date(date_obj):
    months = [
        "Januari", "Februari", "Machi", "Aprili", "Mei", "Juni",
        "Julai", "Agosti", "Septemba", "Oktoba", "Novemba", "Desemba"
    ]
    return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year}"

# --------------------- EXPORT DISCIPLINARY LETTER PDF ---------------------

@admin.action(description="📄Download Disciplinary Letters (PDF)")
def export_disciplinary_letters_pdf(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=barua_za_nidhamu.pdf'

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        rightMargin=25*mm, leftMargin=25*mm,
        topMargin=25*mm, bottomMargin=25*mm,
    )

    elements = []
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'NormalSw', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11,
        leading=14, alignment=TA_JUSTIFY
    )
    title_style = ParagraphStyle(
        'TitleSw', parent=styles['Title'],
        fontName='Helvetica-Bold', alignment=TA_CENTER
    )

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'school_logo.jpg')
    circular_logo_path = None
    if os.path.exists(logo_path):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            circular_logo_path = tmpfile.name
        create_circular_logo(logo_path, circular_logo_path)

    today = swahili_date(datetime.date.today())
    discipline_teachers = Teacher.objects.filter(role='discipline')

    for index, record in enumerate(queryset, start=1):
        student = record.student

        if circular_logo_path and os.path.exists(circular_logo_path):
            img = Image(circular_logo_path, width=35*mm, height=35*mm)
            img.hAlign = 'CENTER'
            elements.append(img)

        elements.append(Paragraph("<b>SHULE YA SEKONDARI PARANGA</b>", title_style))
        elements.append(Paragraph("S.L.P 830, PARANGA – CHEMBA<br/>Simu: 0762 366 411", normal_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Tarehe: <b>{today}</b>", normal_style))
        elements.append(Spacer(1, 12))

        recipient_info = f"""
        <b>Kwa:</b> Mzazi/Mlezi wa<br/>
        <b>Jina la Mwanafunzi:</b> {student.full_name}<br/>
        <b>Namba ya Usajili:</b> {student.admission_number}<br/>
        <b>Darasa:</b> Kidato cha {getattr(student, 'form', '-')} {getattr(student, 'stream', '')}<br/>
        <b>Simu ya Mzazi:</b> {getattr(student, 'parent_contact', '—')}
        """
        elements.append(Paragraph(recipient_info, normal_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>YAH:</b> WITO WA MZAZI KUHUSIANA NA TATIZO LA NIDHAMU", normal_style))
        elements.append(Spacer(1, 10))

        letter_body = f"""
        Ndugu Mzazi/Mlezi,<br/><br/>
        Mtoto wako <b>{student.full_name}</b>, mwanafunzi wa kidato cha <b>{getattr(student, 'form', '-')}</b>, amehusika katika tatizo la nidhamu shuleni.<br/><br/>
        Tafadhali hudhuria shuleni haraka iwezekanavyo kwa mazungumzo na walimu kuhusu tukio hili.<br/><br/>
        <b>Tukio lililoripotiwa:</b><br/>
        “<i>{record.message}</i>”<br/><br/>
        Ni muhimu mzazi awajibike kikamilifu kushiriki katika kutatua tatizo hili. Kukosa kuhudhuria bila taarifa kutachukuliwa kama uzembe na hatua kali zitafuata.<br/><br/>
        Ushirikiano wako ni muhimu kwa mafanikio ya mtoto wako na nidhamu shuleni.<br/><br/>
        Tunathamini usaidizi wako.
        """
        elements.append(Paragraph(letter_body, normal_style))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("Wako mwaminifu,", normal_style))
        elements.append(Spacer(1, 15))

        if discipline_teachers.exists():
            for teacher in discipline_teachers:
                signature = f"______________<br/>{teacher.full_name}<br/>Mwalimu wa Nidhamu<br/>Shule ya Sekondari Paranga"
                elements.append(Paragraph(signature, normal_style))
                elements.append(Spacer(1, 10))
        else:
            elements.append(Paragraph("__________________<br/>Mwl. Nuru Magesa<br/>Mwalimu wa Nidhamu<br/>Shule ya Sekondari Paranga", normal_style))
            elements.append(Spacer(1, 15))

        if index < queryset.count():
            elements.append(PageBreak())

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Oblique', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(A4[0] / 2.0, 15 * mm, "© Paranga Secondary School")
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)

    if circular_logo_path and os.path.exists(circular_logo_path):
        os.remove(circular_logo_path)

    return response


# --------------------- DJANGO ADMIN ---------------------

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "target_group", "is_correction", "attachment", "created_at")
    list_filter = ("target_group", "is_correction", "created_at")
    search_fields = ("title", "message")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    # Optional: send SMS after save
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Only send SMS if newly created
        if not change:
            from .signals import send_announcement_sms
            send_announcement_sms(sender=Announcement, instance=obj, created=True)


@admin.register(DisciplinaryMessage)
class DisciplinaryMessageAdmin(admin.ModelAdmin):
    list_display = ("student_full_name", "admission_number", "created_at", "short_message")
    search_fields = ("student__full_name", "student__admission_number", "message")
    autocomplete_fields = ["student"]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = [export_disciplinary_letters_pdf]

    def student_full_name(self, obj):
        return obj.student.full_name
    student_full_name.short_description = "Jina la Mwanafunzi"

    def admission_number(self, obj):
        return obj.student.admission_number
    admission_number.short_description = "Namba ya Usajili"

    def short_message(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    short_message.short_description = "Ujumbe"
