from __future__ import annotations

import re
from contextvars import ContextVar

_reply_lang: ContextVar[str] = ContextVar("reply_lang", default="en")

_HINDI_ROMAN = {
    "aap", "mujhe", "batao", "bataiye", "karo", "karein", "kya", "kaise",
    "hai", "hain", "nahi", "nahin", "bataye", "batana", "dikhao", "dedo",
    "chahiye", "bata", "mujhko", "aapko", "kripya", "krdo", "krna", "hogya",
    "hoga", "hogi", "wala", "wali", "wale", "kisko", "kiska", "unka", "mera",
}


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "en"
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words:
        return "en"
    strong_hindi = {
        "aap", "mujhe", "batao", "bataiye", "bataye", "btao", "karo", "karein",
        "dikhao", "dedo", "chahiye", "nahi", "nahin", "kya", "kaise", "krdo",
    }
    if any(w in strong_hindi for w in words):
        return "hi"
    hindi_hits = sum(1 for w in words if w in _HINDI_ROMAN)
    if hindi_hits >= 2:
        return "hi"
    return "en"


def set_reply_language(lang: str) -> None:
    _reply_lang.set("hi" if lang == "hi" else "en")


def get_reply_language() -> str:
    return _reply_lang.get()


def language_instruction(lang: str) -> str:
    if lang == "hi":
        return (
            "The user is writing in Hindi/Hinglish. Reply in natural Hindi or Hinglish. "
            "Keep data labels clear."
        )
    return (
        "The user is writing in English. Reply in clear professional English only. "
        "Do not use Hindi or Hinglish words in your response."
    )


def msg(key: str, **kwargs: str) -> str:
    catalog = {
        "select_student": {
            "en": "Please select a student first — search by name and choose the correct student.",
            "hi": "Pehle student select karein — naam se search karke bataiye kaunsa student.",
        },
        "permission_menu": {
            "en": "Sorry, you don't have access to view {label}. Please contact your Branch Admin.",
            "hi": "Maaf kijiye, aapke paas {label} dekhne ki access nahi hai. Apne Branch Admin se permission check karwayein.",
        },
        "permission_fee": {
            "en": "Sorry, you don't have access to view fee information.",
            "hi": "Maaf kijiye, aapke paas fee information dekhne ki access nahi hai.",
        },
        "permission_fee_reports": {
            "en": "Sorry, you don't have access to view fee reports.",
            "hi": "Maaf kijiye, aapke paas fee reports dekhne ki access nahi hai.",
        },
        "permission_attendance": {
            "en": "Sorry, you don't have access to view attendance.",
            "hi": "Maaf kijiye, aapke paas attendance dekhne ki access nahi hai.",
        },
        "permission_exam": {
            "en": "Sorry, you don't have access to view exam results.",
            "hi": "Maaf kijiye, aapke paas exam result dekhne ki access nahi hai.",
        },
        "permission_enquiry": {
            "en": "Sorry, you don't have access to view enquiries.",
            "hi": "Maaf kijiye, aapke paas enquiry list dekhne ki access nahi hai.",
        },
        "chat_limit": {
            "en": "You have reached today's chat limit for this branch ({used}/{limit}). Please try again tomorrow.",
            "hi": "Aaj aap is branch me {limit} chat ki limit reach kar chuke hain ({used}/{limit}). Kal dubara try karein.",
        },
        "generic_error": {
            "en": "Sorry, this request could not be processed right now. Please try again shortly.",
            "hi": "Maaf kijiye, abhi ye request process nahi ho payi. Thodi der baad dubara try karein.",
        },
        "session_expired": {
            "en": "Your session seems to have expired. Please log in to ERP again and reopen the chat.",
            "hi": "Session expire ho gayi lag rahi hai. ERP me dubara login karke chat kholiye.",
        },
        "db_error": {
            "en": "Unable to connect to the ERP database right now. Please contact your administrator.",
            "hi": "Abhi ERP database se connect nahi ho pa raha. Admin se contact karein.",
        },
        "search_min_chars": {
            "en": "Please enter at least 2 characters to search.",
            "hi": "Kam se kam 2 characters likhein.",
        },
        "search_student_prompt": {
            "en": "Type a student name, roll number, or mobile number to search (at least 2 characters).",
            "hi": "Student ka naam, roll number, ya mobile number likhein (kam se kam 2 characters).",
        },
        "dashboard_unavailable": {
            "en": "Dashboard summary could not be loaded right now. Please try again later or contact your administrator.",
            "hi": "Dashboard summary abhi load nahi ho payi. Baad me try karein ya admin se check karwayein.",
        },
        "course_id_required": {
            "en": "Please provide a course ID.",
            "hi": "CourseId batayein.",
        },
    }
    lang = get_reply_language()
    entry = catalog.get(key, {})
    template = entry.get(lang) or entry.get("en") or key
    return template.format(**kwargs)
