from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.decorators import roles_required
from app.extensions import db
from app.models import Attendance, ClassTestResult, Course, CourseRequest, Invoice, LibraryBook, Notice, StudentProfile, TeacherProfile, User

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def student_course_enrollment(student_id, course_id):
    req = CourseRequest.query.filter_by(student_id=student_id, course_id=course_id, status='approved').order_by(CourseRequest.updated_at.desc()).first()
    if not req:
        return None
    overdue = Invoice.query.filter(
        Invoice.student_id == student_id,
        Invoice.course_id == course_id,
        Invoice.status.in_(['unpaid', 'partial', 'overdue']),
        Invoice.due_date < date.today(),
    ).count() > 0
    if overdue and not req.admin_override_active:
        req.enrollment_status = 'suspended'
    elif req.admin_override_active or req.enrollment_status != 'suspended':
        req.enrollment_status = 'active'
    return req


def teacher_course_rows(teacher):
    rows = []
    for course in Course.query.filter_by(teacher_id=teacher.id).order_by(Course.class_name.asc(), Course.code.asc()).all():
        approved_requests = CourseRequest.query.filter_by(course_id=course.id, status='approved').all()
        students = []
        for req in approved_requests:
            if not req.student:
                continue
            enrollment = student_course_enrollment(req.student_id, course.id)
            students.append({
                'id': req.student.id,
                'name': req.student.user.full_name,
                'roll': req.student.admission_no,
                'class_name': req.student.class_name,
                'enrollment_status': enrollment.enrollment_status if enrollment else 'inactive',
            })
        rows.append({'course': course, 'students': students})
    db.session.commit()
    return rows


@dashboard_bp.route("/")
@login_required
def home():
    latest_notices = Notice.query.order_by(Notice.is_pinned.desc(), Notice.published_on.desc()).limit(5).all()

    if current_user.role == 'student' and current_user.student_profile:
        student = current_user.student_profile
        attendance_counts = dict(
            Attendance.query.filter_by(student_id=student.id)
            .with_entities(Attendance.status, func.count(Attendance.id))
            .group_by(Attendance.status)
            .all()
        )
        payment_updates = Invoice.query.filter_by(student_id=student.id).order_by(Invoice.due_date.asc(), Invoice.created_at.desc()).limit(8).all()
        recent_attendance = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.attended_on.desc()).limit(8).all()
        recent_results = ClassTestResult.query.filter_by(student_id=student.id).order_by(ClassTestResult.exam_date.desc()).limit(8).all()
        enrollment_cards = []
        approved_courses = CourseRequest.query.filter_by(student_id=student.id, status='approved').all()
        for req in approved_courses:
            enrollment = student_course_enrollment(student.id, req.course_id)
            if enrollment:
                enrollment_cards.append({'course': req.course, 'status': enrollment.enrollment_status, 'override': enrollment.admin_override_active})
        db.session.commit()
        dashboard_totals = {
            'attendance_present': attendance_counts.get('present', 0),
            'attendance_absent': attendance_counts.get('absent', 0),
            'open_payments': Invoice.query.filter(Invoice.student_id == student.id, Invoice.status.in_(['unpaid', 'partial', 'overdue'])).count(),
            'tests_recorded': ClassTestResult.query.filter_by(student_id=student.id).count(),
        }
        return render_template(
            'dashboard/home.html',
            mode='student',
            student=student,
            latest_notices=latest_notices,
            dashboard_totals=dashboard_totals,
            payment_updates=payment_updates,
            recent_attendance=recent_attendance,
            recent_results=recent_results,
            enrollment_cards=enrollment_cards,
        )

    if current_user.role == 'teacher' and current_user.teacher_profile:
        teacher = current_user.teacher_profile
        teacher_rows = teacher_course_rows(teacher)
        controlled_tests = ClassTestResult.query.filter_by(teacher_id=teacher.id).order_by(ClassTestResult.exam_date.desc()).limit(10).all()
        return render_template('dashboard/home.html', mode='teacher', teacher=teacher, latest_notices=latest_notices, teacher_rows=teacher_rows, controlled_tests=controlled_tests)

    stats = {
        "students": StudentProfile.query.count(),
        "teachers": TeacherProfile.query.count(),
        "courses": Course.query.count(),
        "attendance_records": Attendance.query.count(),
        "pending_invoices": Invoice.query.filter(Invoice.status != "paid").count(),
        "library_books": LibraryBook.query.count(),
    }
    pending_registrations = User.query.filter_by(approval_status="pending").count() if current_user.role == "admin" else 0
    latest_invoices = Invoice.query.order_by(Invoice.due_date.asc()).limit(5).all()
    return render_template(
        "dashboard/home.html",
        mode='staff',
        stats=stats,
        latest_notices=latest_notices,
        latest_invoices=latest_invoices,
        pending_registrations=pending_registrations,
        user_course_requests=[],
    )


@dashboard_bp.post('/teacher/course/<int:course_id>/schedule')
@login_required
@roles_required('teacher')
def teacher_update_schedule(course_id):
    course = Course.query.get_or_404(course_id)
    if not current_user.teacher_profile or course.teacher_id != current_user.teacher_profile.id:
        return ('Forbidden', 403)
    action = (request.form.get('action') or 'running').strip()
    next_schedule_text = (request.form.get('next_schedule_text') or '').strip()
    suspension_note = (request.form.get('suspension_note') or '').strip()
    course.delivery_status = 'suspended' if action == 'suspended' else 'running'
    course.next_schedule_text = next_schedule_text or None
    course.suspension_note = suspension_note or None
    db.session.commit()
    flash(f'Schedule updated for {course.code}.', 'success')
    return redirect(url_for('dashboard.home'))


@dashboard_bp.post('/teacher/course/<int:course_id>/result')
@login_required
@roles_required('teacher')
def teacher_add_result(course_id):
    course = Course.query.get_or_404(course_id)
    if not current_user.teacher_profile or course.teacher_id != current_user.teacher_profile.id:
        return ('Forbidden', 403)
    student_id = int(request.form.get('student_id')) if (request.form.get('student_id') or '').isdigit() else 0
    student = StudentProfile.query.get_or_404(student_id)
    result = ClassTestResult(
        student=student,
        course=course,
        teacher=current_user.teacher_profile,
        test_title=(request.form.get('test_title') or 'Class Test').strip(),
        total_marks=float(request.form.get('total_marks') or 100),
        obtained_marks=float(request.form.get('obtained_marks') or 0),
        grade=(request.form.get('grade') or '').strip() or None,
        exam_date=date.fromisoformat(request.form.get('exam_date')) if request.form.get('exam_date') else date.today(),
        remarks=(request.form.get('remarks') or '').strip() or None,
    )
    db.session.add(result)
    db.session.commit()
    flash(f'Test result saved for {student.user.full_name}.', 'success')
    return redirect(url_for('dashboard.home'))


@dashboard_bp.post('/admin/course-request/<int:request_id>/activate-enrollment')
@login_required
@roles_required('admin')
def activate_enrollment(request_id):
    req = CourseRequest.query.get_or_404(request_id)
    req.enrollment_status = 'active'
    req.admin_override_active = True
    db.session.commit()
    flash('Enrollment has been re-activated by admin.', 'success')
    return redirect(request.referrer or url_for('finance.course_requests_admin'))


@dashboard_bp.route('/admin-hub')
@login_required
@roles_required('admin')
def admin_hub():
    overview = {
        'pending_registrations': User.query.filter_by(approval_status='pending').count(),
        'pending_course_requests': CourseRequest.query.filter(CourseRequest.status.in_(['awaiting_payment', 'pending'])).count(),
        'students': StudentProfile.query.count(),
        'teachers': TeacherProfile.query.count(),
        'courses': Course.query.count(),
        'pending_invoices': Invoice.query.filter(Invoice.status != 'paid').count(),
    }
    recent_requests = CourseRequest.query.order_by(CourseRequest.created_at.desc()).limit(8).all()
    recent_registrations = User.query.order_by(User.created_at.desc()).limit(8).all()
    return render_template('dashboard/admin_hub.html', overview=overview, recent_requests=recent_requests, recent_registrations=recent_registrations)
