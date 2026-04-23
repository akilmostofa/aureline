import os
import requests
from datetime import datetime
from flask import current_app
from flask_mail import Message

from app.extensions import mail


class PaymentService:
    def create_payment(self, provider, payload):
        provider = (provider or "").strip().lower()
        base_map = {
            "bkash": {
                "provider_label": "bKash",
                "pay_to": current_app.config.get("BKASH_PAY_TO", "01XXXXXXXXX"),
                "account_name": current_app.config.get("BKASH_ACCOUNT_NAME", "Aureline Academy"),
                "checkout_url": current_app.config.get("BKASH_PAYMENT_URL"),
                "steps": [
                    "Open your bKash app or dial *247#.",
                    "Choose Send Money or Merchant Payment based on your setup.",
                    "Use the Aureline payment number shown below.",
                    "Pay the exact total amount for this request group.",
                    "Download or convert the payment confirmation screenshot to PDF, then upload it.",
                ],
            },
            "nagad": {
                "provider_label": "Nagad",
                "pay_to": current_app.config.get("NAGAD_PAY_TO", "01XXXXXXXXX"),
                "account_name": current_app.config.get("NAGAD_ACCOUNT_NAME", "Aureline Academy"),
                "checkout_url": current_app.config.get("NAGAD_PAYMENT_URL"),
                "steps": [
                    "Open your Nagad app or dial *167#.",
                    "Choose Send Money or Merchant Pay.",
                    "Use the Aureline payment number shown below.",
                    "Complete the payment for the exact total amount.",
                    "Save the receipt as PDF and upload it for admin verification.",
                ],
            },
            "card": {
                "provider_label": "Card / Online",
                "pay_to": current_app.config.get("CARD_PAYMENT_URL", "https://example.com/aureline-payment"),
                "account_name": current_app.config.get("CARD_ACCOUNT_NAME", "Aureline Academy Online Payments"),
                "checkout_url": current_app.config.get("CARD_PAYMENT_URL"),
                "steps": [
                    "Open the online payment link below.",
                    "Pay the exact amount using debit or credit card.",
                    "Download the payment receipt as PDF.",
                    "Upload the PDF receipt for Aureline verification.",
                ],
            },
            "bank": {
                "provider_label": "Bank Transfer",
                "pay_to": current_app.config.get("BANK_ACCOUNT_NUMBER", "0000000000000"),
                "account_name": current_app.config.get("BANK_ACCOUNT_NAME", "Aureline Academy"),
                "checkout_url": current_app.config.get("BANK_PAYMENT_URL"),
                "steps": [
                    "Transfer the exact amount to the Aureline bank account shown below.",
                    "Keep the transfer receipt or bank slip.",
                    "Convert the receipt to PDF if needed.",
                    "Upload the PDF receipt for admin verification.",
                ],
            },
        }
        data = base_map.get(provider)
        if not data:
            return {"ok": False, "provider": provider, "message": "Unsupported payment provider.", "payload": payload}

        amount = payload.get("amount") or payload.get("total_amount") or "0.00"
        request_group = payload.get("request_group") or "N/A"
        return {
            "ok": True,
            "provider": provider,
            "provider_label": data["provider_label"],
            "message": f"Use {data['provider_label']} to pay BDT {amount} for request {request_group}.",
            "pay_to": data["pay_to"],
            "account_name": data["account_name"],
            "checkout_url": data.get("checkout_url"),
            "steps": data["steps"],
            "amount": amount,
            "payload": payload,
        }

    def handle_webhook(self, provider, payload):
        return {"ok": True, "provider": provider, "message": "Webhook received by scaffold.", "payload": payload}


payment_service = PaymentService()


def build_admin_payment_alert(group_payload):
    courses = group_payload.get("courses", [])
    lines = [
        "New course payment request submitted to Aureline Academy",
        f"Requester: {group_payload.get('requester_name', 'Unknown')} ({group_payload.get('requester_role', 'student')})",
        f"Email: {group_payload.get('requester_email', 'N/A')}",
        f"Mobile: {group_payload.get('payer_mobile', 'N/A')}",
        f"Request Group: {group_payload.get('request_group', 'N/A')}",
        f"Requested For: {group_payload.get('requested_for_name', 'N/A')}",
        f"Class: {group_payload.get('requested_class', 'N/A')}",
        f"Provider / Method: {group_payload.get('payment_provider', '').title()} / {group_payload.get('payment_method', 'N/A')}",
        f"Transaction Ref: {group_payload.get('transaction_ref', 'N/A')}",
        f"Total Amount: BDT {group_payload.get('total_amount', '0.00')}",
        "Courses:",
    ]
    for course in courses:
        lines.append(f"- {course['code']} - {course['title']} (BDT {course['fee']})")
    if group_payload.get("payment_slip_filename"):
        lines.append(f"Slip PDF: {group_payload['payment_slip_filename']}")
    lines.append("Admin review target: within 24 hours")
    return "\n".join(lines)


def build_requester_payment_copy(group_payload):
    courses = group_payload.get("courses", [])
    lines = [
        "Your payment proof has been received by Aureline Academy.",
        "",
        f"Request Group: {group_payload.get('request_group', 'N/A')}",
        f"Student Name: {group_payload.get('requested_for_name', 'N/A')}",
        f"Class: {group_payload.get('requested_class', 'N/A')}",
        f"Payment Provider: {group_payload.get('payment_provider', '').title()}",
        f"Payment Method: {group_payload.get('payment_method', 'N/A')}",
        f"Transaction Ref: {group_payload.get('transaction_ref', 'N/A')}",
        f"Total Amount: BDT {group_payload.get('total_amount', '0.00')}",
        "",
        "Selected Courses:",
    ]
    for course in courses:
        lines.append(f"- {course['code']} - {course['title']} (BDT {course['fee']})")
    lines.extend([
        "",
        "A PDF copy of the submitted payment slip is attached to this email.",
        "Aureline Admin will verify the payment within 24 hours.",
    ])
    return "\n".join(lines)


def build_payment_reminder_message(invoice, recipient_label='Student/Guardian'):
    subject_label = invoice.course.title if invoice.course else 'subject fee'
    return (
        f"Aureline Academy reminder for {recipient_label}: "
        f"Please confirm and complete payment for {subject_label} "
        f"({invoice.course.code if invoice.course else invoice.invoice_no}) by {invoice.due_date.strftime('%d %b %Y')}. "
        f"Amount: BDT {float(invoice.amount or 0):.2f}. "
        f"Billing month: {invoice.billing_month or '-'} ."
    )


def _attach_if_exists(msg, attachment_path=None, attachment_name=None):
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as fh:
            msg.attach(attachment_name or os.path.basename(attachment_path), "application/pdf", fh.read())


def _send_email(subject, body, recipients, attachment_path=None, attachment_name=None):
    if not recipients or not current_app.config.get("MAIL_SERVER"):
        return {"ok": False, "reason": "email_not_configured"}
    msg = Message(subject=subject, recipients=recipients, body=body)
    _attach_if_exists(msg, attachment_path=attachment_path, attachment_name=attachment_name)
    mail.send(msg)
    return {"ok": True, "recipient": ", ".join(recipients)}


def _send_email_alert(subject, body, attachment_path=None, attachment_name=None):
    admin_email = current_app.config.get("ADMIN_ALERT_EMAIL")
    if not admin_email:
        return {"ok": False, "reason": "admin_email_not_configured"}
    return _send_email(subject, body, [admin_email], attachment_path=attachment_path, attachment_name=attachment_name)


def _send_requester_email(group_payload, attachment_path=None, attachment_name=None):
    requester_email = group_payload.get("requester_email")
    if not requester_email:
        return {"ok": False, "reason": "requester_email_missing"}
    return _send_email(
        subject=f"Aureline payment slip copy: {group_payload.get('request_group', 'request')}",
        body=build_requester_payment_copy(group_payload),
        recipients=[requester_email],
        attachment_path=attachment_path,
        attachment_name=attachment_name,
    )


def _send_whatsapp_alert(message):
    phone_number_id = current_app.config.get("WHATSAPP_PHONE_NUMBER_ID")
    access_token = current_app.config.get("WHATSAPP_ACCESS_TOKEN")
    target = current_app.config.get("AURELINE_NOTIFY_WHATSAPP")
    if not phone_number_id or not access_token or not target:
        return {"ok": False, "reason": "whatsapp_not_configured"}
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": target,
        "type": "text",
        "text": {"preview_url": False, "body": message[:4096]},
    }
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    return {"ok": response.ok, "status_code": response.status_code, "response": response.text[:500]}


def send_sms_message(to_number, body):
    api_url = current_app.config.get('SMS_API_URL')
    api_key = current_app.config.get('SMS_API_KEY')
    sender = current_app.config.get('SMS_SENDER_ID')
    if not api_url or not api_key or not to_number:
        current_app.logger.info('SMS not sent because provider is not configured. to=%s body=%s', to_number, body)
        return {'ok': False, 'reason': 'sms_not_configured', 'preview': body}

    payload = {'to': to_number, 'message': body, 'sender_id': sender}
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    response = requests.post(api_url, json=payload, headers=headers, timeout=20)
    return {'ok': response.ok, 'status_code': response.status_code, 'response': response.text[:500]}


def send_admin_payment_notifications(group_payload, attachment_path=None, attachment_name=None):
    message = build_admin_payment_alert(group_payload)
    results = {}
    try:
        results['email'] = _send_email_alert(
            subject=f"Aureline payment request: {group_payload.get('request_group', 'new request')}",
            body=message,
            attachment_path=attachment_path,
            attachment_name=attachment_name,
        )
    except Exception as exc:
        current_app.logger.exception('Failed to send admin payment email alert')
        results['email'] = {'ok': False, 'reason': str(exc)}

    try:
        results['whatsapp'] = _send_whatsapp_alert(message)
    except Exception as exc:
        current_app.logger.exception('Failed to send admin payment WhatsApp alert')
        results['whatsapp'] = {'ok': False, 'reason': str(exc)}
    return results


def send_requester_payment_copy(group_payload, attachment_path=None, attachment_name=None):
    try:
        return _send_requester_email(group_payload, attachment_path=attachment_path, attachment_name=attachment_name)
    except Exception as exc:
        current_app.logger.exception('Failed to send requester payment copy')
        return {'ok': False, 'reason': str(exc)}
