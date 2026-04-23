from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError
from flask_login import login_required
from app.decorators import roles_required
from app.extensions import db
from app.forms import AttendanceForm
from app.models import Attendance, Course, StudentProfile

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


def _student_choices():
    return [(student.id, f"{student.user.full_name} ({student.admission_no})") for student in StudentProfile.query.order_by(StudentProfile.admission_no.asc()).all()]


def _course_choices():
    return [(course.id, f"{course.code} - {course.title}") for course in Course.query.order_by(Course.code.asc()).all()]


def _populate(record, form):
    record.student_id = form.student_id.data
    record.course_id = form.course_id.data
    record.status = form.status.data
    record.attended_on = form.attended_on.data
    record.notes = form.notes.data.strip() if form.notes.data else None


@attendance_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def list_attendance():
    class_name = (request.args.get('class_name') or 'all').strip()
    query = Attendance.query.join(StudentProfile)
    if class_name != 'all':
        query = query.filter(StudentProfile.class_name == class_name)
    records = query.order_by(Attendance.attended_on.desc(), Attendance.id.desc()).all()
    class_options = sorted({student.class_name for student in StudentProfile.query.all()})
    return render_template("attendance/list.html", records=records, class_options=class_options, class_name=class_name)


@attendance_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def create_attendance():
    form = AttendanceForm()
    form.student_id.choices = _student_choices()
    form.course_id.choices = _course_choices()
    if form.validate_on_submit():
        record = Attendance()
        _populate(record, form)
        db.session.add(record)
        try:
            db.session.commit()
            flash("Attendance created successfully.", "success")
            return redirect(url_for("attendance.list_attendance"))
        except IntegrityError:
            db.session.rollback()
            form.attended_on.errors.append("An attendance record already exists for this student, course, and date.")
    return render_template("attendance/form.html", form=form, title="Add Attendance", submit_label="Create Attendance")


@attendance_bp.route("/<int:attendance_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def edit_attendance(attendance_id):
    record = Attendance.query.get_or_404(attendance_id)
    form = AttendanceForm(obj=record)
    form.student_id.choices = _student_choices()
    form.course_id.choices = _course_choices()
    if request.method == "GET":
        form.student_id.data = record.student_id
        form.course_id.data = record.course_id
    if form.validate_on_submit():
        _populate(record, form)
        try:
            db.session.commit()
            flash("Attendance updated successfully.", "success")
            return redirect(url_for("attendance.list_attendance"))
        except IntegrityError:
            db.session.rollback()
            form.attended_on.errors.append("An attendance record already exists for this student, course, and date.")
    return render_template("attendance/form.html", form=form, title="Edit Attendance", submit_label="Update Attendance")


@attendance_bp.route("/<int:attendance_id>/delete", methods=["POST"])
@login_required
@roles_required("admin", "teacher")
def delete_attendance(attendance_id):
    record = Attendance.query.get_or_404(attendance_id)
    db.session.delete(record)
    db.session.commit()
    flash("Attendance deleted successfully.", "warning")
    return redirect(url_for("attendance.list_attendance"))
