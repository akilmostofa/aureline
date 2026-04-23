from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_
from app.decorators import roles_required
from app.extensions import db
from app.forms import CourseForm
from app.models import Course, TeacherProfile

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")


def _teacher_choices():
    choices = [(0, "Unassigned")]
    for teacher in TeacherProfile.query.order_by(TeacherProfile.employee_id.asc()).all():
        choices.append((teacher.id, f"{teacher.user.full_name} ({teacher.employee_id})"))
    return choices


def _code_taken(code, current_id=None):
    query = Course.query.filter(Course.code == code.strip())
    if current_id:
        query = query.filter(Course.id != current_id)
    return db.session.query(query.exists()).scalar()


def _populate(course, form):
    course.title = form.title.data.strip()
    course.code = form.code.data.strip()
    course.class_name = form.class_name.data.strip()
    course.room = form.room.data.strip() if form.room.data else None
    course.schedule_text = form.schedule_text.data.strip() if form.schedule_text.data else None
    course.delivery_status = form.delivery_status.data
    course.next_schedule_text = form.next_schedule_text.data.strip() if form.next_schedule_text.data else None
    course.suspension_note = form.suspension_note.data.strip() if form.suspension_note.data else None
    course.exam_date = form.exam_date.data
    course.description = form.description.data.strip() if form.description.data else None
    course.teacher_id = form.teacher_id.data or None
    course.course_fee = form.course_fee.data
    course.is_open_for_enrollment = bool(form.is_open_for_enrollment.data)


@courses_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def list_courses():
    search = request.args.get("q", "").strip()
    query = Course.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Course.title.ilike(like),
                Course.code.ilike(like),
                Course.class_name.ilike(like),
            )
        )
    courses = query.order_by(Course.class_name.asc(), Course.code.asc()).all()
    return render_template("courses/list.html", courses=courses, search=search)


@courses_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_course():
    form = CourseForm()
    form.teacher_id.choices = _teacher_choices()
    if form.validate_on_submit():
        if _code_taken(form.code.data):
            form.code.errors.append("Course code already exists.")
        else:
            course = Course()
            _populate(course, form)
            db.session.add(course)
            db.session.commit()
            flash("Course created successfully.", "success")
            return redirect(url_for("courses.list_courses"))
    return render_template("courses/form.html", form=form, title="Add Course", submit_label="Create Course")


@courses_bp.route("/<int:course_id>")
@login_required
@roles_required("admin", "teacher")
def detail_course(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template("courses/detail.html", course=course)


@courses_bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    form.teacher_id.choices = _teacher_choices()
    if request.method == "GET":
        form.teacher_id.data = course.teacher_id or 0
        form.delivery_status.data = course.delivery_status
        form.next_schedule_text.data = course.next_schedule_text
        form.suspension_note.data = course.suspension_note
    if form.validate_on_submit():
        if _code_taken(form.code.data, course.id):
            form.code.errors.append("Course code already exists.")
        else:
            _populate(course, form)
            db.session.commit()
            flash("Course updated successfully.", "success")
            return redirect(url_for("courses.detail_course", course_id=course.id))
    return render_template("courses/form.html", form=form, title="Edit Course", submit_label="Update Course")


@courses_bp.route("/<int:course_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted successfully.", "warning")
    return redirect(url_for("courses.list_courses"))
