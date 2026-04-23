from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.decorators import roles_required
from app.extensions import db
from app.forms import LoginForm, RegistrationForm
from app.helpers import generate_student_id, generate_teacher_id, save_profile_image
from app.models import StudentProfile, TeacherProfile, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if user.approval_status != "approved":
                flash("Your registration is pending approval from Aureline Admin.", "warning")
                return render_template("auth/login.html", form=form)
            if not user.is_active:
                flash("Your account is inactive. Please contact Aureline Admin.", "danger")
                return render_template("auth/login.html", form=form)
            login_user(user)
            flash(f"Welcome back, {user.full_name}.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard.home"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email already exists.", "warning")
            return render_template("auth/register.html", form=form)
        if not request.files.get("student_photo") or not request.files.get("guardian_photo"):
            flash("Student and guardian passport pictures are required for student self-registration.", "danger")
            return render_template("auth/register.html", form=form)

        try:
            student_photo_path, student_photo_filename = save_profile_image(request.files.get("student_photo"), "student")
            guardian_photo_path, guardian_photo_filename = save_profile_image(request.files.get("guardian_photo"), "guardian")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            full_name=form.full_name.data.strip(),
            email=email,
            phone=form.phone.data.strip() if form.phone.data else None,
            role="student",
            is_active=False,
            approval_status="pending",
            registration_source="public_registration",
        )
        user.set_password(form.password.data)
        profile = StudentProfile(
            admission_no=generate_student_id(),
            user=user,
            class_name="Pending Assignment",
            guardian_name=form.guardian_name.data.strip(),
            guardian_occupation=form.guardian_occupation.data.strip() if form.guardian_occupation.data else None,
            guardian_phone=form.guardian_phone.data.strip() if form.guardian_phone.data else None,
            parent_email=email,
            current_school_name=form.current_school_name.data.strip() if form.current_school_name.data else None,
            address=form.postal_address.data.strip(),
            fee_status="pending",
            progress_note="Pending Aureline Admin approval.",
            student_photo_path=student_photo_path,
            student_photo_filename=student_photo_filename,
            guardian_photo_path=guardian_photo_path,
            guardian_photo_filename=guardian_photo_filename,
        )
        db.session.add_all([user, profile])
        db.session.commit()
        flash("Student registration submitted. Aureline Admin will review and approve your account.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/pending-users")
@login_required
@roles_required("admin")
def pending_users():
    pending = User.query.filter(User.approval_status.in_(["pending", "rejected"])).order_by(User.created_at.desc()).all()
    approved = User.query.filter_by(approval_status="approved").order_by(User.updated_at.desc()).limit(20).all()
    return render_template("auth/pending_users.html", pending=pending, approved=approved)


@auth_bp.post("/approve/<int:user_id>")
@login_required
@roles_required("admin")
def approve_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.pending_users"))
    user.approval_status = "approved"
    user.is_active = True
    user.approved_at = datetime.utcnow()
    user.approved_by = current_user
    if user.role == "student":
        if not user.student_profile:
            db.session.add(StudentProfile(
                admission_no=generate_student_id(),
                user=user,
                class_name="Pending Assignment",
                guardian_name=user.full_name,
                parent_email=user.email,
                address="Address to be updated by admin",
                fee_status="pending",
                progress_note="Profile auto-created after admin approval.",
            ))
        elif not user.student_profile.admission_no:
            user.student_profile.admission_no = generate_student_id()
    if user.role == "teacher":
        if not user.teacher_profile:
            db.session.add(TeacherProfile(
                employee_id=generate_teacher_id(),
                user=user,
                department="Pending Assignment",
                subject_specialty="Pending Assignment",
                qualification="Pending Verification",
                address="Address to be updated by admin",
            ))
        elif not user.teacher_profile.employee_id:
            user.teacher_profile.employee_id = generate_teacher_id()
    db.session.commit()
    flash(f"Approved account for {user.full_name}.", "success")
    return redirect(url_for("auth.pending_users"))


@auth_bp.post("/reject/<int:user_id>")
@login_required
@roles_required("admin")
def reject_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.pending_users"))
    user.approval_status = "rejected"
    user.is_active = False
    user.approved_at = None
    user.approved_by = current_user
    db.session.commit()
    flash(f"Rejected account for {user.full_name}.", "warning")
    return redirect(url_for("auth.pending_users"))


@auth_bp.post("/toggle-active/<int:user_id>")
@login_required
@roles_required("admin")
def toggle_active(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.pending_users"))
    if user.role == "admin" and user.id == current_user.id:
        flash("You cannot deactivate your own admin account.", "danger")
        return redirect(url_for("auth.pending_users"))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"Updated active status for {user.full_name}.", "info")
    return redirect(url_for("auth.pending_users"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
