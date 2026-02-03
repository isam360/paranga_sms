from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Announcement, DisciplinaryMessage
from teachers.models import Teacher, SchoolClass
from students.models import Student
from core.sms_utils import send_sms
from .utils import normalize_number, form_to_swahili, clean_sms_text

SMS_FOOTER = ""
# SMS_FOOTER = "\n\nUjumbe huu umetumwa rasmi na PARANGASEC."

# ---------------- Helper ----------------
def get_download_url(attachment):
    """
    Force Cloudinary RAW file download for PDF and Excel
    """
    url = attachment.url
    if "/upload/" in url:
        url = url.replace("/upload/", "/upload/fl_attachment/")
    return url


# ================= ANNOUNCEMENT SMS =================
@receiver(post_save, sender=Announcement, dispatch_uid="announcement_sms_once")
def send_announcement_sms(sender, instance, created, **kwargs):
    if not created or instance.sms_sent:
        return

    # Build download link if attachment exists
    attachment_link = ""
    if instance.attachment:
        attachment_link = f"\nDownload: {get_download_url(instance.attachment)}"

    # ---------- TEACHERS ----------
    if instance.target_group in ["teachers", "all", "everyone"]:
        teacher_numbers = list({
            normalize_number(t.phone)
            for t in Teacher.objects.all()
            if normalize_number(t.phone)
        })

        if teacher_numbers:
            try:
                message = clean_sms_text(
                    f"{instance.title}:\n{instance.message}{attachment_link}{SMS_FOOTER}"
                )
                send_sms(teacher_numbers, message)
                print(f"✅ SMS sent to {len(teacher_numbers)} teachers")
            except Exception as e:
                print(f"❌ Failed to send SMS to teachers: {e}")

    # ---------- PARENTS ----------
    if instance.target_group in ["parents", "all", "everyone"]:
        for student in Student.objects.all():
            try:
                number = normalize_number(student.parent_contact)
                if not number:
                    print(f"❌ Invalid parent number for {student.full_name}")
                    continue

                message = clean_sms_text(
                    f"Mzazi wa {student.full_name} ({form_to_swahili(student.form)}),\n"
                    f"{instance.title}:\n{instance.message}{attachment_link}{SMS_FOOTER}"
                )

                send_sms([number], message)
                print(f"✅ SMS sent to parent: {number}")

            except Exception as e:
                print(f"❌ Failed SMS to parent {student.full_name}: {e}")
                continue

    # Mark SMS as sent to prevent duplicates
    instance.sms_sent = True
    instance.save(update_fields=["sms_sent"])


# ================= DISCIPLINARY SMS =================
@receiver(post_save, sender=DisciplinaryMessage, dispatch_uid="disciplinary_sms_once")
def send_disciplinary_sms(sender, instance, created, **kwargs):
    if not created:
        return

    student = instance.student
    number = normalize_number(student.parent_contact)
    if not number:
        print(f"❌ Invalid parent number for disciplinary message: {student.full_name}")
        return

    roman_forms = {1: "I", 2: "II", 3: "III", 4: "IV"}
    form_roman = roman_forms.get(student.form, str(student.form))
    class_name = f"FORM {form_roman}-{student.stream.strip().upper()}"

    try:
        school_class = SchoolClass.objects.get(name=class_name)
        class_teacher = Teacher.objects.get(assigned_class=school_class)
        teacher_info = f"\n\nMwalimu wa darasa: {class_teacher.full_name} ({normalize_number(class_teacher.phone)})"
    except SchoolClass.DoesNotExist:
        teacher_info = "\n\n[Darasa la mwanafunzi halijapatikana.]"
    except Teacher.DoesNotExist:
        teacher_info = "\n\n[Mwalimu wa darasa hajapatikana.]"

    message = clean_sms_text(
        f"Mzazi wa {student.full_name} ({form_to_swahili(student.form)}),\n"
        f"{instance.message}{teacher_info}{SMS_FOOTER}"
    )

    try:
        send_sms([number], message)
        print(f"✅ Disciplinary SMS sent to {number}")
    except Exception as e:
        print(f"❌ Failed disciplinary SMS to {student.full_name}: {e}")




# import phonenumbers
# import unicodedata
# import re
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Announcement, DisciplinaryMessage
# from teachers.models import Teacher, SchoolClass
# from students.models import Student
# from core.sms_utils import send_sms

# # ------------------------------------------
# # 📞 Normalize and Validate Phone Numbers
# # ------------------------------------------
# def normalize_number(number):
#     """
#     Normalize and validate a phone number into E.164 format for Tanzania (+255).
#     Returns None if invalid.
#     """
#     if not number:
#         return None

#     number = str(number).strip().replace(' ', '').replace('-', '')

#     # Convert local format (07XXXXXXXX -> +2557XXXXXXXX)
#     if number.startswith('0'):
#         number = '+255' + number[1:]
#     elif number.startswith('255') and not number.startswith('+'):
#         number = '+' + number

#     try:
#         parsed = phonenumbers.parse(number, None)
#         if phonenumbers.is_valid_number(parsed):
#             return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
#     except phonenumbers.NumberParseException:
#         return None

#     return None

# # ------------------------------------------
# # 🏫 Utility: Convert Form Number to Swahili
# # ------------------------------------------
# def form_to_swahili(form_number):
#     return {
#         1: "Kidato cha Kwanza",
#         2: "Kidato cha Pili",
#         3: "Kidato cha Tatu",
#         4: "Kidato cha Nne",
#     }.get(form_number, f"Form {form_number}")

# # ------------------------------------------
# # ✉️ Clean and Normalize SMS Text (GSM-7 Safe)
# # ------------------------------------------
# GSM_7_BASIC_CHARS = (
#     "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ"
#     "ÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
#     "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà"
# )

# def clean_sms_text(text):
#     """
#     Clean SMS content to GSM-7:
#     - Normalize Unicode
#     - Remove emojis and unsupported symbols
#     - Replace fancy punctuation
#     """
#     if not text:
#         return ""

#     # Normalize unicode (decompose accents)
#     text = unicodedata.normalize('NFKD', text)

#     # Replace common smart punctuation
#     replacements = {
#         '“': '"', '”': '"', '„': '"',
#         '‘': "'", '’': "'", '‚': "'",
#         '–': '-', '—': '-', '―': '-',
#         '…': '...', '•': '-',
#         '\u00A0': ' ',  # non-breaking space
#         '\u200B': '',    # zero-width space
#         '\u200C': '',    # zero-width non-joiner
#         '\u200D': '',    # zero-width joiner
#     }
#     for old, new in replacements.items():
#         text = text.replace(old, new)

#     # Keep only GSM-7 allowed characters
#     text = ''.join(c for c in text if c in GSM_7_BASIC_CHARS or c == '\n')

#     # Remove extra spaces
#     text = re.sub(r'[ \t]+', ' ', text)
#     text = re.sub(r'\n{3,}', '\n\n', text).strip()

#     return text

# # ------------------------------------------
# # 🧾 SMS Footer
# # ------------------------------------------
# SMS_FOOTER = ""
# # \n\nUjumbe huu umetumwa rasmi na PARANGASEC.

# # ------------------------------------------
# # 📢 Send Announcement SMS
# # ------------------------------------------
# @receiver(post_save, sender=Announcement)
# def send_announcement_sms(sender, instance, created, **kwargs):
#     if not created:
#         return

#     # ➤ Teachers
#     if instance.target_group in ['teachers', 'all']:
#         teacher_numbers = [
#             normalize_number(t.phone) for t in Teacher.objects.all()
#             if normalize_number(t.phone)
#         ]
#         if teacher_numbers:
#             message = clean_sms_text(f"{instance.title}:\n{instance.message}{SMS_FOOTER}")
#             try:
#                 send_sms(teacher_numbers, message)
#                 print(f"✅ SMS sent to teachers")
#             except Exception as e:
#                 print(f"❌ Failed to send to teachers: {e}")

#     # ➤ Parents
#     if instance.target_group in ['parents', 'all']:
#         for student in Student.objects.all():
#             number = normalize_number(student.parent_contact)
#             if not number:
#                 print(f"❌ Skipping invalid parent number for {student.full_name}")
#                 continue

#             if instance.is_correction:
#                 message = clean_sms_text(
#                     f"Samahani kwa usumbufu.\n"
#                     f"Ujumbe wa awali kuhusu mwanafunzi {student.full_name} "
#                     f"({form_to_swahili(student.form)}) haukuwa sahihi. Tafadhali puuza ujumbe huo."
#                 )
#             else:
#                 message = clean_sms_text(
#                     f"Mzazi wa {student.full_name} ({form_to_swahili(student.form)}),\n"
#                     f"{instance.title}:\n{instance.message}{SMS_FOOTER}"
#                 )

#             try:
#                 send_sms([number], message)
#                 print(f"✅ SMS sent to parent {number}")
#             except Exception as e:
#                 print(f"❌ Failed to send SMS to {number}: {e}")

# # ------------------------------------------
# # ⚠️ Send Disciplinary SMS
# # ------------------------------------------
# @receiver(post_save, sender=DisciplinaryMessage)
# def send_disciplinary_sms(sender, instance, created, **kwargs):
#     if not created:
#         return

#     student = instance.student
#     number = normalize_number(student.parent_contact)
#     if not number:
#         print(f"❌ Invalid number for {student.full_name}")
#         return

#     roman_forms = {1: "I", 2: "II", 3: "III", 4: "IV"}
#     form_roman = roman_forms.get(student.form, str(student.form))
#     class_name = f"FORM {form_roman}-{student.stream.strip().upper()}"

#     # Class teacher info
#     try:
#         school_class = SchoolClass.objects.get(name=class_name)
#         class_teacher = Teacher.objects.get(assigned_class=school_class)
#         teacher_contact = normalize_number(class_teacher.phone)
#         teacher_info = (
#             f"\n\nMwalimu wa darasa: {class_teacher.full_name}"
#             + (f" ({teacher_contact})" if teacher_contact else "")
#         )
#     except (SchoolClass.DoesNotExist, Teacher.DoesNotExist):
#         teacher_info = "\n\n[Mwalimu wa darasa hajapatikana.]"

#     message = clean_sms_text(
#         f"Mzazi wa {student.full_name} ({form_to_swahili(student.form)}),\n"
#         f"{instance.message}{teacher_info}{SMS_FOOTER}"
#     )

#     try:
#         send_sms([number], message)
#         print(f"✅ Disciplinary SMS sent to {number}")
#     except Exception as e:
#         print(f"❌ Failed to send disciplinary SMS: {e}")



# import phonenumbers
# import unicodedata
# import re
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Announcement, DisciplinaryMessage
# from teachers.models import Teacher, SchoolClass

# from students.models import Student
# from core.sms_utils import send_sms


# def normalize_number(number):
#     """
#     Normalize and validate phone number to E.164 format for Tanzania (+255).
#     Returns None if number is invalid.
#     """
#     if not number:
#         return None
#     number = number.strip()

#     # Handle local Tanzanian format starting with '0'
#     # e.g. '07939585880' -> '+255793958580'
#     if number.startswith('0'):
#         number = '+255' + number[1:]
#     # Also optionally handle if number starts with '00', or includes spaces, etc.
#     # Could strip spaces and + signs already present:
#     number = number.replace(' ', '').replace('-', '')

#     try:
#         parsed = phonenumbers.parse(number, None)  # no default region since we expect +255 or cleaned up
#         if phonenumbers.is_valid_number(parsed):
#             return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
#     except phonenumbers.NumberParseException:
#         pass

#     return None


# def form_to_swahili(form_number):
#     return {
#         1: "Kidato cha Kwanza",
#         2: "Kidato cha Pili",
#         3: "Kidato cha Tatu",
#         4: "Kidato cha Nne",
#     }.get(form_number, f"Form {form_number}")


# def clean_sms_text(text):
#     """
#     Normalize SMS content to plain ASCII to avoid encoding issues.
#     Removes smart quotes, symbols, emojis, and non-ASCII characters.
#     """
#     text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
#     text = re.sub(r'[^\x20-\x7E\n]', '', text)
#     return text


# @receiver(post_save, sender=Announcement)
# def send_announcement_sms(sender, instance, created, **kwargs):
#     if not created:
#         return

#     footer = "\n\nUjumbe huu umetumwa rasmi kupitia mfumo wa PARANGASEC."
#     full_teacher_message = clean_sms_text(f"{instance.title}:\n{instance.message}{footer}")

#     # ➤ Send to Teachers
#     if instance.target_group in ['teachers', 'all']:
#         teacher_numbers = []
#         for t in Teacher.objects.all():
#             n = normalize_number(t.phone)
#             if n:
#                 teacher_numbers.append(n)
#             else:
#                 print(f"❌ Invalid phone number for teacher {t.full_name}: {t.phone}")
#         if teacher_numbers:
#             try:
#                 response = send_sms(teacher_numbers, full_teacher_message)
#                 print(f"✅ SMS sent to teachers: {response}")
#             except Exception as e:
#                 print(f"❌ Failed to send to teachers: {e}")

#     # ➤ Send to Parents
#     if instance.target_group in ['parents', 'all']:
#         parent_contacts = []
#         for s in Student.objects.all():
#             if s.parent_contact:
#                 n = normalize_number(s.parent_contact)
#                 parent_contacts.append({
#                     "number": n,
#                     "name": s.full_name,
#                     "form": form_to_swahili(s.form)
#                 })

#         for parent in parent_contacts:
#             if not parent["number"]:
#                 print(f"❌ Skipping invalid parent number for {parent['name']}")
#                 continue

#             if instance.is_correction:
#                 personalized_message = clean_sms_text(
#                     f"Samahani kwa usumbufu.\n"
#                     f"Ujumbe wa awali kuhusu mwanafunzi {parent['name']} ({parent['form']}) haukuwa sahihi. Tafadhali puuza ujumbe huo."
#                 )
#             else:
#                 personalized_message = clean_sms_text(
#                     f"Mzazi wa {parent['name']} ({parent['form']}),\n"
#                     f"{instance.title}:\n{instance.message}{footer}"
#                 )

#             try:
#                 response = send_sms([parent["number"]], personalized_message)
#                 print(f"✅ SMS sent to parent {parent['number']}: {response}")
#             except Exception as e:
#                 print(f"❌ SMS sending failed to {parent['number']}: {e}")


# @receiver(post_save, sender=DisciplinaryMessage)
# def send_disciplinary_sms(sender, instance, created, **kwargs):
#     if not created:
#         return

#     student = instance.student
#     number = normalize_number(student.parent_contact)
#     if not number:
#         print(f"❌ Invalid number for {student.full_name}: {student.parent_contact}")
#         return

#     # Build class name in the same format as your SchoolClass name field
#     roman_forms = {1: "I", 2: "II", 3: "III", 4: "IV"}
#     form_roman = roman_forms.get(student.form, str(student.form))
#     stream_clean = student.stream.strip().upper()
#     class_name = f"FORM {form_roman}-{stream_clean}"  # e.g. "FORM II-B"
#     print(f"🔍 Looking for class: '{class_name}'")

#     # Try to find the class and teacher
#     try:
#         school_class = SchoolClass.objects.get(name=class_name)
#         class_teacher = Teacher.objects.get(assigned_class=school_class)

#         teacher_name = class_teacher.full_name
#         teacher_phone = normalize_number(class_teacher.phone)

#         if teacher_phone:
#             teacher_contact_info = f"\n\nMwalimu wa darasa: {teacher_name} ({teacher_phone})"
#         else:
#             teacher_contact_info = f"\n\nMwalimu wa darasa: {teacher_name} [Hakuna namba ya simu]"

#     except SchoolClass.DoesNotExist:
#         teacher_contact_info = "\n\n[Darasa la mwanafunzi halijapatikana.]"
#     except Teacher.DoesNotExist:
#         teacher_contact_info = "\n\n[Mwalimu wa darasa hajapangwa bado.]"

#     footer = "\n\nUjumbe huu umetumwa rasmi kupitia mfumo wa PARANGASEC."
#     message = clean_sms_text(
#         f"Mzazi wa {student.full_name} ({form_to_swahili(student.form)}),\n"
#         f"{instance.message}"
#         f"{teacher_contact_info}"
#         f"{footer}"
#     )

#     print(f"➡ Sending SMS to: [{number}]")
#     print(f"➡ Message: {message}")

#     try:
#         response = send_sms([number], message)
#         print(f"✅ Disciplinary SMS sent to {number}: {response}")
#     except Exception as e:
#         print(f"❌ Failed to send disciplinary SMS: {e}")
