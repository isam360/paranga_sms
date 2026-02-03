# announcements/utils.py

import re

# Normalize phone numbers to international format
def normalize_number(number):
    if not number:
        return None
    number = str(number).strip()
    if number.startswith("0"):
        return "+255" + number[1:]
    if number.startswith("255"):
        return "+" + number
    if number.startswith("+"):
        return number
    return None  # invalid format

# Convert form number to Swahili text
def form_to_swahili(form):
    mapping = {1: "Kidato cha Kwanza", 2: "Kidato cha Pili", 3: "Kidato cha Tatu", 4: "Kidato cha Nne"}
    return mapping.get(form, str(form))

# Clean SMS text (remove extra spaces, emojis, etc.)
def clean_sms_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
