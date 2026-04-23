from flask import Blueprint, current_app, jsonify, request
from .services import answer_faq, log_inquiry, send_whatsapp_notification

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


@chatbot_bp.route("/faq", methods=["POST"])
def faq():
    payload = request.get_json(force=True)
    response = answer_faq(payload.get("question", ""), payload.get("language", "en"))
    return jsonify({"answer": response})


@chatbot_bp.route("/conversation-ended", methods=["POST"])
def conversation_ended():
    payload = request.get_json(force=True)
    inquiry = log_inquiry(payload)
    notification = send_whatsapp_notification(payload)
    return jsonify({"inquiry_id": inquiry.id, "notification": notification})


@chatbot_bp.route("/meta/webhook", methods=["GET", "POST"])
def meta_webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if verify_token == current_app.config.get("META_VERIFY_TOKEN"):
            return challenge or "verified", 200
        return "forbidden", 403
    payload = request.get_json(silent=True) or {}
    return jsonify({"ok": True, "received": payload})
