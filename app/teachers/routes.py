from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.decorators import roles_required
from app.extensions import db
from app.forms import TeacherForm
from app.helpers import generate_teacher_id, save_profile_image
from app.models import TeacherProfile, User

teachers_bp = Blueprint("teachers", __name__, url_prefix="/teachers")


def _email_taken(email, current_user_id=None):
    query = User.query.filter(User.email == email.strip().lower())
    if current_user_id:
        query = query.filter(User.id != current_user_id)
    return db.session.query(query.exists()).scalar()


def _employee_taken(employee_id, current_profile_id=None):
    query = TeacherProfile.query.filter(TeacherProfile.employee_id == employee_id.strip())
    if current_profile_id:
        query = query.filter(TeacherProfile.id != current_profile_id)
    return db.session.query(query.exists()).scalar()


def _populate(profile, user, form, is_create=False):
    user.full_name = form.full_name.data.strip()
    user.email = form.email.data.strip().lower()
    user.phone = form.phone.data.strip() if form.phone.data else None
    user.role = "teacher"
    user.approval_status = "approved"
    user.is_active = True
    if is_create or form.password.data:
        user.set_password(form.password.data)

    profile.employee_id = (form.employee_id.data or "").strip() or profile.employee_id or generate_teacher_id()
    profile.department = form.department.data.strip() if form.department.data else None
    profile.subject_specialty = form.subject_specialty.data.strip() if form.subject_specialty.data else None
    profile.qualification = form.qualification.data.strip() if form.qualification.data else None
    profile.join_date = form.join_date.data
    profile.address = form.address.data.strip()
    if request.files.get("teacher_photo") and request.files["teacher_photo"].filename:
        stored, original = save_profile_image(request.files["teacher_photo"], "teacher_admin")
        profile.teacher_photo_path = stored
        profile.teacher_photo_filename = original


@teachers_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def list_teachers():
    search = request.args.get("q", "").strip()
    query = TeacherProfile.query.join(User)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.full_name.ilike(like), User.email.ilike(like), TeacherProfile.employee_id.ilike(like), TeacherProfile.department.ilike(like)))
    teachers = query.order_by(TeacherProfile.created_at.desc()).all()
    return render_template("teachers/list.html", teachers=teachers, search=search)


@teachers_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_teacher():
    form = TeacherForm()
    if form.validate_on_submit():
        employee_id = (form.employee_id.data or "").strip() or generate_teacher_id()
        if not form.password.data:
            form.password.errors.append("Password is required for a new teacher portal account.")
        elif _email_taken(form.email.data):
            form.email.errors.append("Email already exists.")
        elif _employee_taken(employee_id):
            form.employee_id.errors.append("Teacher ID already exists.")
        else:
            try:
                user = User(role="teacher", full_name=form.full_name.data, email=form.email.data, is_active=True, approval_status="approved")
                user.set_password(form.password.data)
                profile = TeacherProfile(user=user, employee_id=employee_id)
                _populate(profile, user, form, is_create=True)
                db.session.add_all([user, profile])
                db.session.commit()
                flash("Teacher created successfully. Teachers can only be registered by Aureline Admin.", "success")
                return redirect(url_for("teachers.list_teachers"))
            except ValueError as exc:
                form.teacher_photo.errors.append(str(exc))
    return render_template("teachers/form.html", form=form, title="Add Teacher", submit_label="Create Teacher")


@teachers_bp.route("/<int:teacher_id>")
@login_required
@roles_required("admin", "teacher")
def detail_teacher(teacher_id):
    teacher = TeacherProfile.query.get_or_404(teacher_id)
    return render_template("teachers/detail.html", teacher=teacher)


@teachers_bp.route("/<int:teacher_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_teacher(teacher_id):
    teacher = TeacherProfile.query.get_or_404(teacher_id)
    form = TeacherForm(obj=teacher)
    if request.method == "GET":
        form.full_name.data = teacher.user.full_name
        form.email.data = teacher.user.email
        form.phone.data = teacher.user.phone
        form.address.data = teacher.address
    if form.validate_on_submit():
        employee_id = (form.employee_id.data or "").strip() or teacher.employee_id or generate_teacher_id()
        if _email_taken(form.email.data, teacher.user_id):
            form.email.errors.append("Email already exists.")
        elif _employee_taken(employee_id, teacher.id):
            form.employee_id.errors.append("Teacher ID already exists.")
        else:
            try:
                form.employee_id.data = employee_id
                _populate(teacher, teacher.user, form)
                db.session.commit()
                flash("Teacher updated successfully.", "success")
                return redirect(url_for("teachers.detail_teacher", teacher_id=teacher.id))
            except ValueError as exc:
                form.teacher_photo.errors.append(str(exc))
    return render_template("teachers/form.html", form=form, title="Edit Teacher", submit_label="Update Teacher")


@teachers_bp.route("/<int:teacher_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_teacher(teacher_id):
    teacher = TeacherProfile.query.get_or_404(teacher_id)
    db.session.delete(teacher.user)
    db.session.commit()
    flash("Teacher deleted successfully.", "warning")
    return redirect(url_for("teachers.list_teachers"))
