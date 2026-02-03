"""
Professional SMS Utilities for Exam Results
Fully Updated & Africa’s Talking Compatible
"""

import re
import unicodedata
from datetime import datetime
from core.sms_utils import send_sms
from announcements.signals import normalize_number, form_to_swahili
from results.models import ExamResult
from students.models import Student

# =======================================================
# GSM-7 CHARACTER SET
# =======================================================

GSM_7_BASIC = (
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ"
    " !\"#¤%&'()*+,-./0123456789:;<=>?"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿"
    "abcdefghijklmnopqrstuvwxyzäöñüà"
)
GSM_7_EXT = "^{}\\[~]|€"
GSM_7 = set(GSM_7_BASIC + GSM_7_EXT)

GSM_SMS_LIMIT = 160
UCS2_SMS_LIMIT = 70
SMS_LOG_FILE = "sms_sent.log"

# =======================================================
# LOGGING
# =======================================================

def log_sms(number: str, message: str, status: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SMS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] To: {number} | Status: {status} | Message: {message}\n")

# =======================================================
# SANITIZATION
# =======================================================

def sanitize_unicode(text: str) -> str:
    if not text:
        return ""

    # Normalize & remove accents
    text = unicodedata.normalize("NFKD", text)
    text = ''.join(c for c in text if not unicodedata.combining(c))

    # Replace known problematic symbols
    REPLACEMENTS = {
        "—": "-", "–": "-", "…": "...",
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "·": "-", "`": "'", "´": "'",
        "\u00A0": " ", "\u200B": "", "\u200C": "", "\u200D": "", "\u2060": "",
        "$": "", "£": "", "€": "", "¥": "Y", "¢": "c",
        "©": "(c)", "®": "(R)", "™": "(TM)"
    }
    for bad, good in REPLACEMENTS.items():
        text = text.replace(bad, good)

    # Remove anything outside safe GSM-7 + punctuation
    allowed = set(GSM_7) | set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ") | set(",.!?;:'\"-()|")
    text = ''.join(c for c in text if c in allowed)

    # Collapse spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text

def is_gsm7(text: str) -> bool:
    return all(c in GSM_7 for c in text)

def final_clean(text: str) -> str:
    text = sanitize_unicode(text)
    text = text.replace("\n", " | ")
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"^\W+|\W+$", "", text)
    return text.strip()

def prepare_sms_payload(text: str) -> str:
    return final_clean(text)

# =======================================================
# NECTA POINTS & DIVISIONS
# =======================================================

def necta_points(score: float) -> int:
    if score is None: return 0
    if score >= 75: return 1
    if score >= 65: return 2
    if score >= 45: return 3
    if score >= 30: return 4
    return 5

def get_division(total_points: int) -> str:
    if total_points <= 17: return "Daraja 1"
    if total_points <= 21: return "Daraja 2"
    if total_points <= 25: return "Daraja 3"
    if total_points <= 33: return "Daraja 4"
    return "Daraja 0"

# =======================================================
# BUILD STUDENT SMS
# =======================================================

def build_student_sms(student: Student, exam_session) -> str | None:
    results = ExamResult.objects.filter(
        student=student,
        assignment__exam_session=exam_session
    ).select_related("assignment__subject")

    if not results.exists():
        return None

    student_name = sanitize_unicode(student.full_name)
    form_name = sanitize_unicode(form_to_swahili(student.form))
    term_name = sanitize_unicode(exam_session.term)

    subject_scores, points_list = [], []

    for r in results:
        score = r.score
        subject_name = sanitize_unicode(r.assignment.subject.code.strip())
        if len(subject_name) > 12:
            subject_name = subject_name[:12]
        subject_scores.append((subject_name, score))
        if score is not None:
            points_list.append(necta_points(score))

    best7 = sorted(points_list)[:7]
    total_points = sum(best7)

    valid_scores = [s for _, s in subject_scores if s is not None]
    mean_score = round(sum(valid_scores) / max(1, len(valid_scores)), 1)

    division = get_division(total_points)

    # Class ranking
    classmates = Student.objects.filter(
        form=exam_session.form,
        stream=exam_session.stream,
        status="active"
    )
    ranking = []
    for s in classmates:
        rs = ExamResult.objects.filter(student=s, assignment__exam_session=exam_session)
        totals = [necta_points(r.score) for r in rs if r.score is not None]
        b7 = sum(sorted(totals)[:7]) if totals else 9999
        ranking.append((s.id, b7))
    ranking.sort(key=lambda x: x[1])
    position = next(i for i, item in enumerate(ranking, start=1) if item[0] == student.id)

    # Build message
    msg_parts = [
        f"Matokeo ya {student_name}",
        f"{form_name} | {term_name} {exam_session.year}"
    ]
    for subject, score in subject_scores:
        msg_parts.append(f"{subject}: {score if score is not None else 'NA'}")
    msg_parts.append(f"Pointi: {total_points} | Wastani: {mean_score}")
    msg_parts.append(f"Daraja: {division} | Nafasi Darasani: {position}")

    msg = " | ".join(msg_parts)
    return final_clean(msg)

# =======================================================
# SMART SPLIT & SEND SMS
# =======================================================

def split_sms(message: str) -> list[str]:
    """
    Split SMS into chunks at | separator to avoid breaking subjects
    """
    limit = GSM_SMS_LIMIT if is_gsm7(message) else UCS2_SMS_LIMIT
    parts = message.split(" | ")
    chunks = []
    current = ""

    for part in parts:
        part_with_sep = part if current == "" else " | " + part
        if len(current + part_with_sep) > limit:
            if current:
                chunks.append(current.strip())
            current = part
        else:
            current += part_with_sep

    if current:
        chunks.append(current.strip())

    return chunks
def send_student_sms(student: Student, exam_session) -> str:
    number = normalize_number(student.parent_contact)
    if not number:
        log_sms("N/A", "No number", "Failed")
        return f"Invalid number for {student.full_name} (Parent: {student.parent_name})"

    msg = build_student_sms(student, exam_session)
    if not msg:
        log_sms(number, "No results", "Failed")
        return f"No results for {student.full_name} (Parent: {student.parent_name})"

    safe_message = prepare_sms_payload(msg)
    messages_chunks = split_sms(safe_message)

    for chunk in messages_chunks:
        try:
            send_sms([number], chunk)
            log_sms(number, chunk, f"Sent to {student.parent_name}")
        except Exception as e:
            log_sms(number, chunk, f"Failed: {str(e)}")

    return f"Sent to {student.full_name} (Parent: {student.parent_name}, {len(messages_chunks)} SMS)"

# def send_student_sms(student: Student, exam_session) -> str:
#     number = normalize_number(student.parent_contact)
#     if not number:
#         log_sms("N/A", "No number", "Failed")
#         return f"Invalid number for {student.full_name}"

#     msg = build_student_sms(student, exam_session)
#     if not msg:
#         log_sms(number, "No results", "Failed")
#         return f"No results for {student.full_name}"

#     safe_message = prepare_sms_payload(msg)
#     messages = split_sms(safe_message)

#     for chunk in messages:
#         try:
#             send_sms([number], chunk)
#             log_sms(number, chunk, "Sent")
#         except Exception as e:
#             log_sms(number, chunk, f"Failed: {str(e)}")

#     return f"Sent to {student.full_name} ({len(messages)} SMS)"
