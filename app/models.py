from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db, login_manager


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    approval_status = db.Column(db.String(20), default="approved", nullable=False, index=True)
    registration_source = db.Column(db.String(20), default="admin_created", nullable=False)
    approved_at = db.Column(db.DateTime)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    approved_by = db.relationship("User", remote_side=[id], backref="approved_users")
    student_profile = db.relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = db.relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    submitted_course_requests = db.relationship("CourseRequest", foreign_keys="CourseRequest.requester_user_id", back_populates="requester")
    reviewed_course_requests = db.relationship("CourseRequest", foreign_keys="CourseRequest.reviewed_by_user_id", back_populates="reviewed_by")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_role_badge(self):
        return self.role.title()

    def get_status_badge(self):
        return self.approval_status.title()


class StudentProfile(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admission_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(20))
    guardian_name = db.Column(db.String(120), nullable=False)
    guardian_occupation = db.Column(db.String(120))
    guardian_phone = db.Column(db.String(20))
    parent_email = db.Column(db.String(120))
    current_school_name = db.Column(db.String(150))
    address = db.Column(db.Text, nullable=False)
    fee_status = db.Column(db.String(30), default="pending", nullable=False)
    progress_note = db.Column(db.Text)
    student_photo_path = db.Column(db.String(255))
    student_photo_filename = db.Column(db.String(255))
    guardian_photo_path = db.Column(db.String(255))
    guardian_photo_filename = db.Column(db.String(255))

    user = db.relationship("User", back_populates="student_profile")
    attendances = db.relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", back_populates="student", cascade="all, delete-orphan")
    course_requests = db.relationship("CourseRequest", back_populates="student", cascade="all, delete-orphan")
    test_results = db.relationship("ClassTestResult", back_populates="student", cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.user.full_name} ({self.admission_no})"


class TeacherProfile(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    department = db.Column(db.String(120))
    subject_specialty = db.Column(db.String(120))
    qualification = db.Column(db.String(120))
    join_date = db.Column(db.Date)
    address = db.Column(db.Text, nullable=False)
    teacher_photo_path = db.Column(db.String(255))
    teacher_photo_filename = db.Column(db.String(255))

    user = db.relationship("User", back_populates="teacher_profile")
    courses = db.relationship("Course", back_populates="teacher", cascade="all")
    test_results = db.relationship("ClassTestResult", back_populates="teacher")

    def __str__(self):
        return f"{self.user.full_name} ({self.employee_id})"


class Course(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    class_name = db.Column(db.String(50), nullable=False)
    room = db.Column(db.String(50))
    schedule_text = db.Column(db.String(120))
    delivery_status = db.Column(db.String(20), default="running", nullable=False)
    next_schedule_text = db.Column(db.String(120))
    suspension_note = db.Column(db.Text)
    exam_date = db.Column(db.Date)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher_profile.id"))
    zoom_meeting_id = db.Column(db.String(120))
    course_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    is_open_for_enrollment = db.Column(db.Boolean, nullable=False, default=True)

    teacher = db.relationship("TeacherProfile", back_populates="courses")
    attendances = db.relationship("Attendance", back_populates="course", cascade="all, delete-orphan")
    requests = db.relationship("CourseRequest", back_populates="course", cascade="all, delete-orphan")
    recordings = db.relationship("RecordedClassVideo", back_populates="course", cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", back_populates="course")
    test_results = db.relationship("ClassTestResult", back_populates="course")

    def __str__(self):
        return f"{self.code} - {self.title}"


class Attendance(TimestampMixin, db.Model):
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "attended_on", name="uq_attendance_student_course_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    attended_on = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)

    student = db.relationship("StudentProfile", back_populates="attendances")
    course = db.relationship("Course", back_populates="attendances")


class Invoice(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    billing_month = db.Column(db.String(20), index=True)
    status = db.Column(db.String(30), default="unpaid", nullable=False)
    payment_provider = db.Column(db.String(30))
    payment_method = db.Column(db.String(30))
    transaction_ref = db.Column(db.String(120))
    paid_on = db.Column(db.Date)
    notes = db.Column(db.Text)
    reminder_sent_at = db.Column(db.DateTime)

    student = db.relationship("StudentProfile", back_populates="invoices")
    course = db.relationship("Course", back_populates="invoices")


class CourseRequest(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_group = db.Column(db.String(50), nullable=False, index=True)
    requester_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"))
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    course_fee = db.Column(db.Numeric(10, 2), nullable=False)
    payment_provider = db.Column(db.String(30), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)
    transaction_ref = db.Column(db.String(120), nullable=False, index=True)
    payer_mobile = db.Column(db.String(20))
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    admin_note = db.Column(db.Text)
    requested_for_name = db.Column(db.String(120))
    requested_class = db.Column(db.String(50))
    reviewed_at = db.Column(db.DateTime)
    payment_slip_path = db.Column(db.String(255))
    payment_slip_filename = db.Column(db.String(255))
    payment_slip_uploaded_at = db.Column(db.DateTime)
    enrollment_status = db.Column(db.String(20), default="active", nullable=False)
    admin_override_active = db.Column(db.Boolean, default=False, nullable=False)

    requester = db.relationship("User", foreign_keys=[requester_user_id], back_populates="submitted_course_requests")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_user_id], back_populates="reviewed_course_requests")
    student = db.relationship("StudentProfile", back_populates="course_requests")
    course = db.relationship("Course", back_populates="requests")


class ClassTestResult(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher_profile.id"))
    test_title = db.Column(db.String(150), nullable=False)
    total_marks = db.Column(db.Numeric(6, 2), nullable=False, default=100)
    obtained_marks = db.Column(db.Numeric(6, 2), nullable=False)
    grade = db.Column(db.String(10))
    exam_date = db.Column(db.Date, nullable=False)
    remarks = db.Column(db.Text)

    student = db.relationship("StudentProfile", back_populates="test_results")
    course = db.relationship("Course", back_populates="test_results")
    teacher = db.relationship("TeacherProfile", back_populates="test_results")


class RecordedClassVideo(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    subject_label = db.Column(db.String(120), nullable=False)
    zoom_meeting_id = db.Column(db.String(120))
    recording_date = db.Column(db.Date, nullable=False)
    video_url = db.Column(db.String(500), nullable=False)
    duration_minutes = db.Column(db.Integer)
    source = db.Column(db.String(30), default="zoom", nullable=False)
    access_scope = db.Column(db.String(20), default="class_only", nullable=False)
    notes = db.Column(db.Text)

    course = db.relationship("Course", back_populates="recordings")


class LibraryBook(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    isbn = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(80))
    shelf = db.Column(db.String(40))
    published_year = db.Column(db.Integer)
    description = db.Column(db.Text)
    copies_total = db.Column(db.Integer, default=1, nullable=False)
    copies_available = db.Column(db.Integer, default=1, nullable=False)


class Notice(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    audience = db.Column(db.String(30), default="all", nullable=False)
    message = db.Column(db.Text, nullable=False)
    published_on = db.Column(db.Date, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)


class ChatInquiry(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(120))
    visitor_email = db.Column(db.String(120))
    visitor_mobile = db.Column(db.String(20))
    channel = db.Column(db.String(20))
    language = db.Column(db.String(5), default="en")
    transcript = db.Column(db.Text)
    status = db.Column(db.String(50), default="seeking_guidance")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
