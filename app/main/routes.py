from flask import Blueprint, render_template
from flask_login import current_user
from app.models import Course, Notice, StudentProfile, TeacherProfile

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    stats = {
        "students": StudentProfile.query.count(),
        "teachers": TeacherProfile.query.count(),
        "courses": Course.query.count(),
        "notices": Notice.query.count(),
    }
    notices = Notice.query.order_by(Notice.is_pinned.desc(), Notice.published_on.desc()).limit(3).all()
    running_courses = Course.query.filter_by(delivery_status="running").order_by(Course.class_name.asc(), Course.code.asc()).limit(6).all()
    course_cards = []
    for course in running_courses:
        enrolled_count = len({req.student_id for req in course.requests if req.status == "approved" and req.student_id})
        course_cards.append({
            "code": course.code,
            "title": course.title,
            "class_name": course.class_name,
            "time": course.schedule_text or course.next_schedule_text or "Schedule TBD",
            "students": enrolled_count,
        })
    return render_template("main/index.html", stats=stats, notices=notices, current_user=current_user, course_cards=course_cards)
