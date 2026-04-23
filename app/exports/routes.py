from datetime import date
from flask import Blueprint, request, send_file
from flask_login import login_required, current_user
from app.decorators import roles_required
from sqlalchemy import or_
from app.models import Attendance, ClassTestResult, CourseRequest, Invoice, StudentProfile, TeacherProfile, User
from app.pdf_utils import build_pdf

exports_bp = Blueprint('exports', __name__, url_prefix='/exports')


def _finance_rows(class_name='all'):
    query = Invoice.query.join(StudentProfile)
    if class_name != 'all':
        query = query.filter(StudentProfile.class_name == class_name)
    invoices = query.order_by(Invoice.due_date.asc(), Invoice.created_at.desc()).all()
    rows = []
    for invoice in invoices:
        rows.append([
            invoice.invoice_no,
            invoice.student.user.full_name if invoice.student and invoice.student.user else '-',
            invoice.student.class_name if invoice.student else '-',
            invoice.course.code if invoice.course else '-',
            invoice.course.title if invoice.course else (invoice.notes or '-'),
            f"BDT {float(invoice.amount or 0):.2f}",
            invoice.billing_month or '-',
            invoice.due_date.strftime('%d %b %Y') if invoice.due_date else '-',
            invoice.status.title(),
        ])
    return rows


@exports_bp.route('/students.pdf')
@login_required
@roles_required('admin', 'teacher')
def students_pdf():
    class_name = (request.args.get('class_name') or 'all').strip()
    search = (request.args.get('q') or '').strip()
    query = StudentProfile.query
    if class_name != 'all':
        query = query.filter(StudentProfile.class_name == class_name)
    if search:
        like = f"%{search}%"
        query = query.join(User).filter(or_(User.full_name.ilike(like), User.email.ilike(like), StudentProfile.admission_no.ilike(like), StudentProfile.class_name.ilike(like)))
    students = query.order_by(StudentProfile.class_name.asc(), StudentProfile.admission_no.asc()).all()
    rows = [[s.admission_no, s.user.full_name, s.class_name, s.section or '-', s.guardian_name, s.user.phone or '-', s.fee_status.title()] for s in students]
    pdf = build_pdf('Aureline Academy - Student Directory', filters={'Class': class_name, 'Search': search}, headers=['ID', 'Name', 'Class', 'Section', 'Guardian', 'Mobile', 'Fee Status'], rows=rows)
    return send_file(pdf, as_attachment=True, download_name='aureline-students.pdf', mimetype='application/pdf')




@exports_bp.route('/teachers.pdf')
@login_required
@roles_required('admin', 'teacher')
def teachers_pdf():
    teachers = TeacherProfile.query.order_by(TeacherProfile.employee_id.asc()).all()
    rows = [[t.employee_id, t.user.full_name, t.department or '-', t.subject_specialty or '-', t.user.phone or '-', t.address] for t in teachers]
    pdf = build_pdf('Aureline Academy - Teacher Directory', headers=['ID', 'Name', 'Department', 'Subject', 'Phone', 'Address'], rows=rows)
    return send_file(pdf, as_attachment=True, download_name='aureline-teachers.pdf', mimetype='application/pdf')


@exports_bp.route('/attendance.pdf')
@login_required
@roles_required('admin', 'teacher')
def attendance_pdf():
    class_name = (request.args.get('class_name') or 'all').strip()
    query = Attendance.query.join(StudentProfile)
    if class_name != 'all':
        query = query.filter(StudentProfile.class_name == class_name)
    records = query.order_by(Attendance.attended_on.desc()).all()
    rows = [[
        item.attended_on.strftime('%d %b %Y'),
        item.student.user.full_name,
        item.student.class_name,
        item.course.code,
        item.course.title,
        item.status.title(),
        item.notes or '-',
    ] for item in records]
    pdf = build_pdf('Aureline Academy - Attendance Report', filters={'Class': class_name}, headers=['Date', 'Student', 'Class', 'Subject Code', 'Subject', 'Status', 'Notes'], rows=rows)
    return send_file(pdf, as_attachment=True, download_name='aureline-attendance.pdf', mimetype='application/pdf')


@exports_bp.route('/finance.pdf')
@login_required
@roles_required('admin')
def finance_pdf():
    class_name = (request.args.get('class_name') or 'all').strip()
    pdf = build_pdf('Aureline Academy - Finance Report', filters={'Class': class_name}, headers=['Invoice', 'Student', 'Class', 'Code', 'Subject', 'Amount', 'Billing Month', 'Due Date', 'Status'], rows=_finance_rows(class_name=class_name))
    return send_file(pdf, as_attachment=True, download_name='aureline-finance.pdf', mimetype='application/pdf')


@exports_bp.route('/payments.pdf')
@login_required
@roles_required('admin')
def payments_pdf():
    status = (request.args.get('status') or 'all').strip()
    query = CourseRequest.query.order_by(CourseRequest.created_at.desc())
    if status != 'all':
        query = query.filter(CourseRequest.status == status)
    items = query.all()
    rows = [[
        item.request_group,
        item.requested_for_name or (item.student.user.full_name if item.student else '-'),
        item.requested_class or '-',
        item.course.code,
        item.course.title,
        f"BDT {float(item.course_fee or 0):.2f}",
        item.payment_provider.title(),
        item.transaction_ref,
        item.status.replace('_', ' ').title(),
    ] for item in items]
    pdf = build_pdf('Aureline Academy - Course Payment Requests', filters={'Status': status}, headers=['Request', 'Student', 'Class', 'Code', 'Subject', 'Fee', 'Provider', 'Transaction', 'Status'], rows=rows)
    return send_file(pdf, as_attachment=True, download_name='aureline-course-payments.pdf', mimetype='application/pdf')


@exports_bp.route('/reports-summary.pdf')
@login_required
@roles_required('admin', 'teacher')
def reports_summary_pdf():
    class_name = (request.args.get('class_name') or 'all').strip()
    attendance_rows = []
    for row in Attendance.query.join(StudentProfile).order_by(Attendance.attended_on.desc()).limit(20).all():
        if class_name != 'all' and row.student.class_name != class_name:
            continue
        attendance_rows.append([row.attended_on.strftime('%d %b %Y'), row.student.user.full_name, row.student.class_name, row.course.code, row.status.title()])
    pdf = build_pdf('Aureline Academy - Dynamic Report Summary', subtitle=f'Generated on {date.today().strftime("%d %b %Y")}', filters={'Class': class_name}, headers=['Date', 'Student', 'Class', 'Subject', 'Attendance'], rows=attendance_rows)
    return send_file(pdf, as_attachment=True, download_name='aureline-report-summary.pdf', mimetype='application/pdf')


@exports_bp.route('/student-dashboard.pdf')
@login_required
def student_dashboard_pdf():
    if current_user.role not in {'student', 'admin'}:
        return ('Forbidden', 403)
    student = current_user.student_profile
    if current_user.role == 'admin' and request.args.get('student_id', '').isdigit():
        student = StudentProfile.query.get_or_404(int(request.args['student_id']))
    if not student:
        return ('Student profile not found', 404)
    rows = []
    latest_results = ClassTestResult.query.filter_by(student_id=student.id).order_by(ClassTestResult.exam_date.desc()).limit(10).all()
    latest_invoices = Invoice.query.filter_by(student_id=student.id).order_by(Invoice.due_date.asc()).limit(10).all()
    latest_attendance = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.attended_on.desc()).limit(10).all()
    for record in latest_attendance:
        rows.append([f"Attendance | {record.attended_on.strftime('%d %b %Y')}", record.course.code, record.status.title(), record.notes or '-'])
    for invoice in latest_invoices:
        rows.append([f"Payment | {invoice.billing_month or '-'}", invoice.course.code if invoice.course else '-', invoice.status.title(), f"BDT {float(invoice.amount or 0):.2f}"])
    for result in latest_results:
        rows.append([f"Test | {result.exam_date.strftime('%d %b %Y')}", result.course.code, f"{float(result.obtained_marks):.2f}/{float(result.total_marks):.2f}", result.grade or '-'])
    pdf = build_pdf(f'Aureline Academy - Student Dashboard ({student.user.full_name})', filters={'Student ID': student.admission_no, 'Class': student.class_name}, headers=['Type', 'Subject', 'Status / Score', 'Notes'], rows=rows)
    return send_file(pdf, as_attachment=True, download_name=f'{student.admission_no}-dashboard.pdf', mimetype='application/pdf')
