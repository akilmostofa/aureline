from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.decorators import roles_required
from app.extensions import db
from app.forms import StudentForm
from app.helpers import generate_student_id, save_profile_image
from app.models import StudentProfile, User

students_bp = Blueprint("students", __name__, url_prefix="/students")


def _email_taken(email, current_user_id=None):
    query = User.query.filter(User.email == email.strip().lower())
    if current_user_id:
        query = query.filter(User.id != current_user_id)
    return db.session.query(query.exists()).scalar()


def _admission_taken(admission_no, current_profile_id=None):
    query = StudentProfile.query.filter(StudentProfile.admission_no == admission_no.strip())
    if current_profile_id:
        query = query.filter(StudentProfile.id != current_profile_id)
    return db.session.query(query.exists()).scalar()


def _populate(profile, user, form, is_create=False):
    user.full_name = form.full_name.data.strip()
    user.email = form.email.data.strip().lower()
    user.phone = form.phone.data.strip() if form.phone.data else None
    user.role = "student"
    user.approval_status = user.approval_status or "approved"
    user.is_active = True
    if is_create or form.password.data:
        user.set_password(form.password.data)

    profile.admission_no = (form.admission_no.data or "").strip() or profile.admission_no or generate_student_id()
    profile.class_name = form.class_name.data.strip()
    profile.section = form.section.data.strip() if form.section.data else None
    profile.guardian_name = form.guardian_name.data.strip()
    profile.guardian_occupation = form.guardian_occupation.data.strip() if form.guardian_occupation.data else None
    profile.guardian_phone = form.guardian_phone.data.strip() if form.guardian_phone.data else None
    profile.parent_email = form.parent_email.data.strip().lower() if form.parent_email.data else None
    profile.current_school_name = form.current_school_name.data.strip() if form.current_school_name.data else None
    profile.address = form.address.data.strip()
    profile.fee_status = form.fee_status.data
    profile.progress_note = form.progress_note.data.strip() if form.progress_note.data else None

    if request.files.get("student_photo") and request.files["student_photo"].filename:
        stored, original = save_profile_image(request.files["student_photo"], "student_admin")
        profile.student_photo_path = stored
        profile.student_photo_filename = original
    if request.files.get("guardian_photo") and request.files["guardian_photo"].filename:
        stored, original = save_profile_image(request.files["guardian_photo"], "guardian_admin")
        profile.guardian_photo_path = stored
        profile.guardian_photo_filename = original


@students_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def list_students():
    search = request.args.get("q", "").strip()
    class_name = (request.args.get("class_name") or "all").strip()
    query = StudentProfile.query.join(User)
    if class_name != "all":
        query = query.filter(StudentProfile.class_name == class_name)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.full_name.ilike(like), User.email.ilike(like), StudentProfile.admission_no.ilike(like), StudentProfile.class_name.ilike(like)))
    students = query.order_by(StudentProfile.created_at.desc()).all()
    class_options = sorted({student.class_name for student in StudentProfile.query.all()})
    return render_template("students/list.html", students=students, search=search, class_name=class_name, class_options=class_options)


@students_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_student():
    form = StudentForm()
    if form.validate_on_submit():
        admission_no = (form.admission_no.data or "").strip() or generate_student_id()
        if not form.password.data:
            form.password.errors.append("Password is required for a new student portal account.")
        elif _email_taken(form.email.data):
            form.email.errors.append("Email already exists.")
        elif _admission_taken(admission_no):
            form.admission_no.errors.append("Student ID already exists.")
        else:
            try:
                user = User(role="student", full_name=form.full_name.data, email=form.email.data, is_active=True, approval_status="approved")
                user.set_password(form.password.data)
                profile = StudentProfile(user=user, admission_no=admission_no)
                _populate(profile, user, form, is_create=True)
                db.session.add_all([user, profile])
                db.session.commit()
                flash("Student created successfully.", "success")
                return redirect(url_for("students.list_students"))
            except ValueError as exc:
                form.student_photo.errors.append(str(exc))
    return render_template("students/form.html", form=form, title="Add Student", submit_label="Create Student")


@students_bp.route("/<int:student_id>")
@login_required
@roles_required("admin", "teacher")
def detail_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    return render_template("students/detail.html", student=student)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    form = StudentForm(obj=student)
    if request.method == "GET":
        form.full_name.data = student.user.full_name
        form.email.data = student.user.email
        form.phone.data = student.user.phone
        form.guardian_occupation.data = student.guardian_occupation
    if form.validate_on_submit():
        admission_no = (form.admission_no.data or "").strip() or student.admission_no or generate_student_id()
        if _email_taken(form.email.data, student.user_id):
            form.email.errors.append("Email already exists.")
        elif _admission_taken(admission_no, student.id):
            form.admission_no.errors.append("Student ID already exists.")
        else:
            try:
                form.admission_no.data = admission_no
                _populate(student, student.user, form)
                db.session.commit()
                flash("Student updated successfully.", "success")
                return redirect(url_for("students.detail_student", student_id=student.id))
            except ValueError as exc:
                form.student_photo.errors.append(str(exc))
    return render_template("students/form.html", form=form, title="Edit Student", submit_label="Update Student")


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    db.session.delete(student.user)
    db.session.commit()
    flash("Student deleted successfully.", "warning")
    return redirect(url_for("students.list_students"))
