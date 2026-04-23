from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, DateField, DecimalField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    full_name = StringField("Student Full Name", validators=[DataRequired(), Length(max=120)])
    email = EmailField("Student Email", validators=[DataRequired(), Email()])
    phone = StringField("Student Mobile Number", validators=[Optional(), Length(max=20)])
    role = SelectField("Apply As", choices=[("student", "Student")], validators=[DataRequired()])
    guardian_name = StringField("Guardian Name", validators=[DataRequired(), Length(max=120)])
    guardian_occupation = StringField("Guardian Occupation", validators=[Optional(), Length(max=120)])
    guardian_phone = StringField("Guardian Mobile Number", validators=[Optional(), Length(max=20)])
    current_school_name = StringField("Current School Name", validators=[Optional(), Length(max=150)])
    postal_address = TextAreaField("Postal Address", validators=[DataRequired()])
    student_photo = FileField("Student Passport Picture", validators=[FileAllowed(IMAGE_TYPES, "Upload JPG, PNG, or WEBP image only.")])
    guardian_photo = FileField("Guardian Passport Picture", validators=[FileAllowed(IMAGE_TYPES, "Upload JPG, PNG, or WEBP image only.")])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")])
    submit = SubmitField("Submit Registration")


class StudentForm(FlaskForm):
    full_name = StringField("Student Name", validators=[DataRequired(), Length(max=120)])
    email = EmailField("Portal Email", validators=[DataRequired(), Email()])
    password = PasswordField("Portal Password", validators=[Optional(), Length(min=6, max=128)])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    admission_no = StringField("Student ID", validators=[Optional(), Length(max=50)])
    class_name = StringField("Class", validators=[DataRequired(), Length(max=50)])
    section = StringField("Section", validators=[Optional(), Length(max=20)])
    guardian_name = StringField("Guardian Name", validators=[DataRequired(), Length(max=120)])
    guardian_occupation = StringField("Guardian Occupation", validators=[Optional(), Length(max=120)])
    guardian_phone = StringField("Guardian Phone", validators=[Optional(), Length(max=20)])
    parent_email = EmailField("Guardian Email", validators=[Optional(), Email()])
    current_school_name = StringField("Current School Name", validators=[Optional(), Length(max=150)])
    address = TextAreaField("Postal Address", validators=[DataRequired()])
    student_photo = FileField("Student Passport Picture", validators=[FileAllowed(IMAGE_TYPES, "Upload JPG, PNG, or WEBP image only.")])
    guardian_photo = FileField("Guardian Passport Picture", validators=[FileAllowed(IMAGE_TYPES, "Upload JPG, PNG, or WEBP image only.")])
    fee_status = SelectField("Fee Status", choices=[("pending", "Pending"), ("partial", "Partial"), ("paid", "Paid")], validators=[DataRequired()])
    progress_note = TextAreaField("Progress Note", validators=[Optional()])
    submit = SubmitField("Save Student")


class TeacherForm(FlaskForm):
    full_name = StringField("Teacher Name", validators=[DataRequired(), Length(max=120)])
    email = EmailField("Portal Email", validators=[DataRequired(), Email()])
    password = PasswordField("Portal Password", validators=[Optional(), Length(min=6, max=128)])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    employee_id = StringField("Teacher ID", validators=[Optional(), Length(max=50)])
    department = StringField("Department", validators=[Optional(), Length(max=120)])
    subject_specialty = StringField("Subject Specialty", validators=[Optional(), Length(max=120)])
    qualification = StringField("Qualification", validators=[Optional(), Length(max=120)])
    join_date = DateField("Join Date", validators=[Optional()])
    address = TextAreaField("Postal Address", validators=[DataRequired()])
    teacher_photo = FileField("Teacher Passport Picture", validators=[FileAllowed(IMAGE_TYPES, "Upload JPG, PNG, or WEBP image only.")])
    submit = SubmitField("Save Teacher")


class CourseForm(FlaskForm):
    title = StringField("Course Title", validators=[DataRequired(), Length(max=120)])
    code = StringField("Course Code", validators=[DataRequired(), Length(max=50)])
    class_name = StringField("Class", validators=[DataRequired(), Length(max=50)])
    room = StringField("Room", validators=[Optional(), Length(max=50)])
    schedule_text = StringField("Schedule", validators=[Optional(), Length(max=120)])
    delivery_status = SelectField("Class Delivery Status", choices=[("running", "Running"), ("suspended", "Suspended")], validators=[DataRequired()])
    next_schedule_text = StringField("Next Schedule", validators=[Optional(), Length(max=120)])
    suspension_note = TextAreaField("Schedule Note", validators=[Optional()])
    exam_date = DateField("Exam Date", validators=[Optional()])
    teacher_id = SelectField("Teacher", coerce=int, validators=[Optional()])
    course_fee = DecimalField("Course Fee (BDT)", validators=[DataRequired(), NumberRange(min=0)], places=2)
    is_open_for_enrollment = BooleanField("Open for Enrollment", default=True)
    zoom_meeting_id = StringField("Zoom Meeting ID", validators=[Optional(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Save Course")


class AttendanceForm(FlaskForm):
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    course_id = SelectField("Course", coerce=int, validators=[DataRequired()])
    status = SelectField("Status", choices=[("present", "Present"), ("absent", "Absent"), ("late", "Late")], validators=[DataRequired()])
    attended_on = DateField("Attendance Date", validators=[DataRequired()], default=date.today)
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save Attendance")


class InvoiceForm(FlaskForm):
    invoice_no = StringField("Invoice No", validators=[DataRequired(), Length(max=50)])
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    course_id = SelectField("Subject / Course", coerce=int, validators=[Optional()])
    billing_month = StringField("Billing Month", validators=[Optional(), Length(max=20)], description="Use format like 2026-04")
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0)], places=2)
    due_date = DateField("Due Date", validators=[DataRequired()], default=date.today)
    status = SelectField("Status", choices=[("unpaid", "Unpaid"), ("partial", "Partial"), ("paid", "Paid")], validators=[DataRequired()])
    payment_provider = SelectField("Payment Provider", choices=[("", "Select"), ("bkash", "bKash"), ("nagad", "Nagad"), ("card", "Card"), ("cash", "Cash"), ("bank", "Bank")], validators=[Optional()])
    payment_method = StringField("Payment Method", validators=[Optional(), Length(max=30)])
    transaction_ref = StringField("Transaction Ref", validators=[Optional(), Length(max=120)])
    paid_on = DateField("Paid On", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save Invoice")


class LibraryBookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    author = StringField("Author", validators=[DataRequired(), Length(max=120)])
    isbn = StringField("ISBN", validators=[Optional(), Length(max=50)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    shelf = StringField("Shelf", validators=[Optional(), Length(max=40)])
    published_year = StringField("Published Year", validators=[Optional(), Length(max=4)])
    description = TextAreaField("Description", validators=[Optional()])
    copies_total = StringField("Total Copies", validators=[DataRequired()])
    copies_available = StringField("Available Copies", validators=[DataRequired()])
    submit = SubmitField("Save Book")


class NoticeForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    audience = SelectField("Audience", choices=[("all", "All"), ("students", "Students"), ("teachers", "Teachers")], validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    published_on = DateField("Publish Date", validators=[DataRequired()], default=date.today)
    is_pinned = BooleanField("Pin Notice")
    submit = SubmitField("Save Notice")
