import os
from datetime import date, datetime

from flask import Flask
from config import Config
from .admin import setup_admin
from .extensions import cache, db, limiter, login_manager, mail, migrate
from .finance.services import build_payment_reminder_message, send_sms_message
from .models import CourseRequest, Invoice
from .seed import seed_demo_data


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, app.config["PAYMENT_SLIP_UPLOAD_FOLDER"]), exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, app.config["PROFILE_UPLOAD_FOLDER"]), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."

    from .main.routes import main_bp
    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .students.routes import students_bp
    from .teachers.routes import teachers_bp
    from .courses.routes import courses_bp
    from .attendance.routes import attendance_bp
    from .finance.routes import finance_bp
    from .library.routes import library_bp
    from .communication.routes import communication_bp
    from .reports.routes import reports_bp
    from .integrations.routes import integrations_bp
    from .chatbot.routes import chatbot_bp
    from .exports.routes import exports_bp

    for blueprint in [
        main_bp,
        auth_bp,
        dashboard_bp,
        students_bp,
        teachers_bp,
        courses_bp,
        attendance_bp,
        finance_bp,
        library_bp,
        communication_bp,
        reports_bp,
        integrations_bp,
        chatbot_bp,
        exports_bp,
    ]:
        app.register_blueprint(blueprint)

    setup_admin(app)

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Seed demo users and records."""
        seed_demo_data()
        print("Seeded demo users and records.")

    @app.cli.command("generate-monthly-subject-invoices")
    def generate_monthly_subject_invoices():
        """Generate subject-wise monthly invoices for approved course requests."""
        billing_month = datetime.utcnow().strftime("%Y-%m")
        due_date = date.today().replace(day=min(10, date.today().day if date.today().day > 0 else 10))
        created = 0
        seen_pairs = set()
        approved_records = CourseRequest.query.filter_by(status="approved").order_by(CourseRequest.student_id.asc(), CourseRequest.course_id.asc()).all()
        for record in approved_records:
            if not record.student_id or not record.course_id:
                continue
            key = (record.student_id, record.course_id)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            existing = Invoice.query.filter_by(student_id=record.student_id, course_id=record.course_id, billing_month=billing_month).first()
            if existing:
                continue
            invoice = Invoice(
                invoice_no=f"INV-{billing_month.replace('-', '')}-{record.student_id}-{record.course_id}",
                student_id=record.student_id,
                course_id=record.course_id,
                amount=record.course_fee,
                due_date=due_date,
                billing_month=billing_month,
                status="unpaid",
                notes=f"Monthly subject fee for {record.course.code} ({billing_month})",
            )
            db.session.add(invoice)
            created += 1
        db.session.commit()
        print(f"Generated {created} monthly subject invoice(s) for {billing_month}.")

    @app.cli.command("send-payment-reminders")
    def send_payment_reminders():
        """Send subject-wise payment reminder SMS three days before due date."""
        target_due = date.today().toordinal() + 3
        invoices = Invoice.query.filter(Invoice.status.in_(["unpaid", "partial"])).all()
        sent = 0
        for invoice in invoices:
            if not invoice.due_date or invoice.due_date.toordinal() != target_due or invoice.reminder_sent_at:
                continue
            recipients = []
            if invoice.student and invoice.student.user and invoice.student.user.phone:
                recipients.append((invoice.student.user.phone, "Student"))
            if invoice.student and invoice.student.guardian_phone:
                recipients.append((invoice.student.guardian_phone, "Guardian"))
            successful = False
            for phone, label in recipients:
                result = send_sms_message(phone, build_payment_reminder_message(invoice, recipient_label=label))
                if result.get("ok"):
                    successful = True
                    sent += 1
            if successful:
                invoice.reminder_sent_at = datetime.utcnow()
        db.session.commit()
        print(f"Sent {sent} reminder SMS message(s).")

    return app
