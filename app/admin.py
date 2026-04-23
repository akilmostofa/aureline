from flask import redirect, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user
from sqlalchemy import func

from .extensions import db
from .models import Attendance, ChatInquiry, ClassTestResult, Course, CourseRequest, Invoice, LibraryBook, Notice, RecordedClassVideo, StudentProfile, TeacherProfile, User


class SecureAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not self.is_accessible():
            return self.inaccessible_callback("index")

        stats = {
            "users": db.session.query(func.count(User.id)).scalar() or 0,
            "students": db.session.query(func.count(StudentProfile.id)).scalar() or 0,
            "teachers": db.session.query(func.count(TeacherProfile.id)).scalar() or 0,
            "courses": db.session.query(func.count(Course.id)).scalar() or 0,
            "pending_users": db.session.query(func.count(User.id)).filter(User.approval_status == "pending").scalar() or 0,
            "pending_payments": db.session.query(func.count(CourseRequest.id)).filter(CourseRequest.status.in_(["pending", "awaiting_payment"])).scalar() or 0,
            "unpaid_invoices": db.session.query(func.count(Invoice.id)).filter(Invoice.status == "unpaid").scalar() or 0,
            "books": db.session.query(func.count(LibraryBook.id)).scalar() or 0,
            "recordings": db.session.query(func.count(RecordedClassVideo.id)).scalar() or 0,
        }

        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_requests = CourseRequest.query.order_by(CourseRequest.created_at.desc()).limit(5).all()
        return self.render("admin/index.html", stats=stats, recent_users=recent_users, recent_requests=recent_requests)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login", next=request.url))


class SecureModelView(ModelView):
    can_export = True
    page_size = 25
    create_modal = False
    edit_modal = False
    can_view_details = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login", next=request.url))


class UserAdminView(SecureModelView):
    column_list = ["full_name", "email", "role", "approval_status", "is_active", "registration_source", "approved_at"]
    column_filters = ["role", "approval_status", "is_active", "registration_source"]
    form_columns = ["full_name", "email", "role", "phone", "is_active", "approval_status", "registration_source", "approved_at", "approved_by"]


class StudentAdminView(SecureModelView):
    column_list = ["admission_no", "user", "class_name", "current_school_name", "guardian_name", "guardian_occupation", "address", "fee_status"]
    form_columns = ["admission_no", "user", "class_name", "section", "guardian_name", "guardian_occupation", "guardian_phone", "parent_email", "current_school_name", "address", "fee_status", "progress_note", "student_photo_filename", "guardian_photo_filename"]


class TeacherAdminView(SecureModelView):
    column_list = ["employee_id", "user", "department", "subject_specialty", "address", "join_date"]
    form_columns = ["employee_id", "user", "department", "subject_specialty", "qualification", "join_date", "address", "teacher_photo_filename"]


class CourseAdminView(SecureModelView):
    column_list = ["code", "title", "class_name", "course_fee", "delivery_status", "is_open_for_enrollment", "teacher", "schedule_text", "next_schedule_text"]
    column_filters = ["class_name", "is_open_for_enrollment", "delivery_status"]
    form_columns = ["title", "code", "class_name", "course_fee", "delivery_status", "next_schedule_text", "suspension_note", "is_open_for_enrollment", "room", "schedule_text", "exam_date", "description", "teacher", "zoom_meeting_id"]


class CourseRequestAdminView(SecureModelView):
    column_list = ["request_group", "requester", "requested_for_name", "requested_class", "course", "course_fee", "payment_provider", "transaction_ref", "payment_slip_filename", "status", "enrollment_status", "reviewed_at"]
    column_filters = ["status", "payment_provider", "requested_class", "enrollment_status"]
    form_columns = ["request_group", "requester", "student", "course", "course_fee", "payment_provider", "payment_method", "transaction_ref", "payer_mobile", "payment_slip_filename", "payment_slip_path", "payment_slip_uploaded_at", "status", "enrollment_status", "admin_override_active", "requested_for_name", "requested_class", "admin_note", "reviewed_by", "reviewed_at"]


class InvoiceAdminView(SecureModelView):
    column_list = ["invoice_no", "student", "course", "billing_month", "amount", "due_date", "status", "payment_provider", "transaction_ref", "reminder_sent_at"]
    column_filters = ["status", "payment_provider", "due_date", "billing_month"]
    form_columns = ["invoice_no", "student", "course", "billing_month", "amount", "due_date", "status", "payment_provider", "payment_method", "transaction_ref", "paid_on", "notes", "reminder_sent_at"]


class ClassTestResultAdminView(SecureModelView):
    column_list = ["student", "course", "test_title", "obtained_marks", "total_marks", "grade", "exam_date"]
    column_filters = ["course", "grade", "exam_date"]
    form_columns = ["student", "course", "teacher", "test_title", "obtained_marks", "total_marks", "grade", "exam_date", "remarks"]


class RecordingAdminView(SecureModelView):
    column_list = ["title", "course", "class_name", "subject_label", "recording_date", "source", "video_url"]
    column_filters = ["class_name", "subject_label", "source", "access_scope"]
    form_columns = ["course", "title", "class_name", "subject_label", "zoom_meeting_id", "recording_date", "video_url", "duration_minutes", "source", "access_scope", "notes"]


def setup_admin(app):
    admin = Admin(app, name="Aureline Admin", template_mode="bootstrap4", index_view=SecureAdminIndexView(name="Admin Panel", endpoint="admin", url="/admin/"))
    admin.add_link(MenuLink(name="Back to Website", url="/dashboard/admin-hub"))
    admin.add_link(MenuLink(name="Logout", url="/auth/logout"))
    admin.add_view(UserAdminView(User, db.session, category="Accounts", endpoint="admin_users"))
    admin.add_view(StudentAdminView(StudentProfile, db.session, category="Academics", endpoint="admin_students"))
    admin.add_view(TeacherAdminView(TeacherProfile, db.session, category="Academics", endpoint="admin_teachers"))
    admin.add_view(CourseAdminView(Course, db.session, category="Academics", endpoint="admin_courses"))
    admin.add_view(SecureModelView(Attendance, db.session, category="Academics", endpoint="admin_attendance"))
    admin.add_view(ClassTestResultAdminView(ClassTestResult, db.session, category="Academics", endpoint="admin_test_results"))
    admin.add_view(RecordingAdminView(RecordedClassVideo, db.session, category="Academics", endpoint="admin_recordings"))
    admin.add_view(InvoiceAdminView(Invoice, db.session, category="Finance", endpoint="admin_invoices"))
    admin.add_view(CourseRequestAdminView(CourseRequest, db.session, category="Finance", endpoint="admin_course_requests"))
    admin.add_view(SecureModelView(LibraryBook, db.session, category="Library", endpoint="admin_books"))
    admin.add_view(SecureModelView(Notice, db.session, category="Communication", endpoint="admin_notices"))
    admin.add_view(SecureModelView(ChatInquiry, db.session, category="Chatbot", endpoint="admin_inquiries"))
