from flask import current_app
from app.extensions import db
from app.models import ChatInquiry


def answer_faq(question, language="en"):
    faq = {
        "fees": {
            "en": "You can review tuition invoices from the finance module or request the payment portal link from the school office.",
            "bn": "আপনি ফাইন্যান্স মডিউল থেকে টিউশন ইনভয়েস দেখতে পারবেন বা স্কুল অফিস থেকে পেমেন্ট পোর্টালের লিংক নিতে পারবেন।",
        },
        "admission": {
            "en": "Admission support is available from the admissions desk. Please share your class interest and student details.",
            "bn": "ভর্তি সহায়তার জন্য অনুগ্রহ করে শ্রেণি ও শিক্ষার্থীর তথ্য জানান।",
        },
        "zoom": {
            "en": "Zoom class links are available from the course dashboard once meetings are scheduled.",
            "bn": "জুম ক্লাস লিংক কোর্স ড্যাশবোর্ডে পাওয়া যাবে।",
        },
    }
    normalized = (question or "").lower()
    matched_key = "admission"
    for key in faq:
        if key in normalized:
            matched_key = key
            break
    return faq[matched_key].get(language, faq[matched_key]["en"])


def log_inquiry(payload):
    inquiry = ChatInquiry(
        visitor_name=payload.get("name"),
        visitor_email=payload.get("email"),
        visitor_mobile=payload.get("mobile"),
        channel=payload.get("channel", "web"),
        language=payload.get("language", "en"),
        transcript=payload.get("transcript"),
        status=payload.get("status", "seeking_guidance"),
    )
    db.session.add(inquiry)
    db.session.commit()
    return inquiry


def aureline_notification_message(payload):
    return "\n".join([
        "New inquiry received:",
        f"Name: {payload.get('name', 'Unknown')}",
        f"Email: {payload.get('email', 'N/A')}",
        f"Mobile: {payload.get('mobile', 'N/A')}",
        "Status: Seeking Aureline Academy guidance",
    ])


def send_whatsapp_notification(payload):
    return {
        "ok": True,
        "target": current_app.config.get("AURELINE_NOTIFY_WHATSAPP", "not-configured"),
        "message": aureline_notification_message(payload),
    }
