from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import extract, func
from app.decorators import roles_required
from app.models import Attendance, ClassTestResult, Course, CourseRequest, Invoice, StudentProfile

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def summary():
    selected_class = (request.args.get("class_name") or "all").strip()

    fee_query = Invoice.query.join(StudentProfile)
    attendance_query = Attendance.query.join(StudentProfile, Attendance.student_id == StudentProfile.id)
    result_query = ClassTestResult.query.join(StudentProfile, ClassTestResult.student_id == StudentProfile.id)
    student_count_query = StudentProfile.query

    if selected_class != "all":
        fee_query = fee_query.filter(StudentProfile.class_name == selected_class)
        attendance_query = attendance_query.filter(StudentProfile.class_name == selected_class)
        result_query = result_query.filter(StudentProfile.class_name == selected_class)
        student_count_query = student_count_query.filter(StudentProfile.class_name == selected_class)

    fee_breakdown = fee_query.with_entities(Invoice.status, func.count(Invoice.id)).group_by(Invoice.status).order_by(Invoice.status.asc()).all()
    attendance_breakdown = attendance_query.with_entities(Attendance.status, func.count(Attendance.id)).group_by(Attendance.status).order_by(Attendance.status.asc()).all()
    class_breakdown = StudentProfile.query.with_entities(StudentProfile.class_name, func.count(StudentProfile.id)).group_by(StudentProfile.class_name).order_by(StudentProfile.class_name.asc()).all()
    monthly_collections_raw = fee_query.with_entities(extract('month', Invoice.created_at), func.coalesce(func.sum(Invoice.amount), 0)).filter(Invoice.status == 'paid').group_by(extract('month', Invoice.created_at)).order_by(extract('month', Invoice.created_at)).all()
    request_status_breakdown = CourseRequest.query.with_entities(CourseRequest.status, func.count(CourseRequest.id)).group_by(CourseRequest.status).order_by(CourseRequest.status.asc()).all()
    course_enrollments = Course.query.with_entities(Course.code, Course.title, func.count(CourseRequest.id)).outerjoin(CourseRequest, CourseRequest.course_id == Course.id).group_by(Course.id, Course.code, Course.title).order_by(func.count(CourseRequest.id).desc(), Course.code.asc()).limit(8).all()
    test_result_summary = result_query.with_entities(Course.code, func.avg(ClassTestResult.obtained_marks), func.avg(ClassTestResult.total_marks), func.count(ClassTestResult.id)).join(Course, Course.id == ClassTestResult.course_id).group_by(Course.code).order_by(Course.code.asc()).all()

    totals = {
        'students': student_count_query.count(),
        'courses': Course.query.count(),
        'paid_amount': float(sum(float(invoice.amount or 0) for invoice in fee_query.filter(Invoice.status == 'paid').all())),
        'open_requests': CourseRequest.query.filter(CourseRequest.status.in_(['awaiting_payment', 'pending'])).count(),
    }
    class_options = [row[0] for row in class_breakdown]
    chart_data = {
        'invoice_labels': [label.title() for label, _ in fee_breakdown],
        'invoice_values': [count for _, count in fee_breakdown],
        'attendance_labels': [label.title() for label, _ in attendance_breakdown],
        'attendance_values': [count for _, count in attendance_breakdown],
        'monthly_labels': [f"Month {int(month)}" for month, _ in monthly_collections_raw],
        'monthly_values': [float(total or 0) for _, total in monthly_collections_raw],
        'request_labels': [label.replace('_', ' ').title() for label, _ in request_status_breakdown],
        'request_values': [count for _, count in request_status_breakdown],
    }
    return render_template(
        "reports/summary.html",
        fee_breakdown=fee_breakdown,
        attendance_breakdown=attendance_breakdown,
        class_breakdown=class_breakdown,
        course_enrollments=course_enrollments,
        totals=totals,
        class_options=class_options,
        selected_class=selected_class,
        chart_data=chart_data,
        test_result_summary=test_result_summary,
    )
