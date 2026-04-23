from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal
import os

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.decorators import roles_required
from app.extensions import db
from app.forms import InvoiceForm
from app.models import Course, CourseRequest, Invoice, StudentProfile
from .services import payment_service, send_admin_payment_notifications, send_requester_payment_copy

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")


def _student_choices():
    return [
        (student.id, f"{student.user.full_name} ({student.admission_no})")
        for student in StudentProfile.query.order_by(StudentProfile.admission_no.asc()).all()
    ]




def _course_choices():
    return [(0, 'General / No Subject')] + [
        (course.id, f"{course.code} - {course.title}")
        for course in Course.query.order_by(Course.code.asc()).all()
    ]

def _invoice_taken(invoice_no, current_id=None):
    query = Invoice.query.filter(Invoice.invoice_no == invoice_no.strip())
    if current_id:
        query = query.filter(Invoice.id != current_id)
    return db.session.query(query.exists()).scalar()


def _populate(invoice, form):
    invoice.invoice_no = form.invoice_no.data.strip()
    invoice.student_id = form.student_id.data
    invoice.course_id = form.course_id.data or None
    invoice.billing_month = form.billing_month.data.strip() if form.billing_month.data else None
    invoice.amount = form.amount.data
    invoice.due_date = form.due_date.data
    invoice.status = form.status.data
    invoice.payment_provider = form.payment_provider.data or None
    invoice.payment_method = form.payment_method.data.strip() if form.payment_method.data else None
    invoice.transaction_ref = form.transaction_ref.data.strip() if form.transaction_ref.data else None
    invoice.paid_on = form.paid_on.data
    invoice.notes = form.notes.data.strip() if form.notes.data else None


def _accessible_students_for_user(user):
    if user.role == "student":
        return [user.student_profile] if user.student_profile else []
    return []


def _available_courses_for_student(student=None):
    query = Course.query.filter_by(is_open_for_enrollment=True)
    if student and student.class_name and student.class_name != "Pending Assignment":
        query = query.filter(Course.class_name == student.class_name)
    return query.order_by(Course.class_name.asc(), Course.code.asc()).all()


def _group_requests(requests):
    groups = OrderedDict()
    for item in requests:
        bucket = groups.setdefault(
            item.request_group,
            {
                "group": item.request_group,
                "status": item.status,
                "requester": item.requester,
                "student": item.student,
                "requested_for_name": item.requested_for_name,
                "requested_class": item.requested_class,
                "payment_provider": item.payment_provider,
                "payment_method": item.payment_method,
                "transaction_ref": item.transaction_ref,
                "payer_mobile": item.payer_mobile,
                "created_at": item.created_at,
                "reviewed_at": item.reviewed_at,
                "admin_note": item.admin_note,
                "items": [],
                "total": Decimal("0.00"),
                "payment_slip_filename": item.payment_slip_filename,
                "payment_slip_path": item.payment_slip_path,
                "payment_slip_uploaded_at": item.payment_slip_uploaded_at,
                "enrollment_status": item.enrollment_status,
                "first_request_id": item.id,
            },
        )
        bucket["items"].append(item)
        bucket["total"] += item.course_fee or Decimal("0.00")
        status_priority = {"rejected": 4, "approved": 3, "pending": 2, "awaiting_payment": 1}
        if status_priority.get(item.status, 0) > status_priority.get(bucket["status"], 0):
            bucket["status"] = item.status
        if item.reviewed_at and (not bucket["reviewed_at"] or item.reviewed_at > bucket["reviewed_at"]):
            bucket["reviewed_at"] = item.reviewed_at
        if item.admin_note:
            bucket["admin_note"] = item.admin_note
        if item.payment_slip_filename and not bucket["payment_slip_filename"]:
            bucket["payment_slip_filename"] = item.payment_slip_filename
            bucket["payment_slip_path"] = item.payment_slip_path
            bucket["payment_slip_uploaded_at"] = item.payment_slip_uploaded_at
        if item.payment_provider and item.payment_provider != 'pending' and bucket["payment_provider"] in (None, '', 'pending'):
            bucket["payment_provider"] = item.payment_provider
            bucket["payment_method"] = item.payment_method
            bucket["transaction_ref"] = item.transaction_ref
            bucket["payer_mobile"] = item.payer_mobile
        if item.enrollment_status == 'suspended':
            bucket["enrollment_status"] = 'suspended'
    return list(groups.values())


def _next_invoice_no():
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    count = Invoice.query.count() + 1
    return f"INV-{stamp}-{count:03d}"


def _payment_slip_directory():
    return os.path.join(current_app.instance_path, current_app.config["PAYMENT_SLIP_UPLOAD_FOLDER"])


def _save_payment_slip(file_storage, request_group):
    if not file_storage or not file_storage.filename:
        return None, None
    filename = secure_filename(file_storage.filename)
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Payment slip must be uploaded as a PDF file.")
    stored_name = f"{request_group}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    absolute_path = os.path.join(_payment_slip_directory(), stored_name)
    file_storage.save(absolute_path)
    return stored_name, filename


def _build_group_payload(group_records):
    first = group_records[0]
    return {
        "request_group": first.request_group,
        "requester_name": first.requester.full_name,
        "requester_role": first.requester.role,
        "requester_email": first.requester.email,
        "payer_mobile": first.payer_mobile or first.requester.phone,
        "requested_for_name": first.requested_for_name,
        "requested_class": first.requested_class,
        "payment_provider": first.payment_provider,
        "payment_method": first.payment_method,
        "transaction_ref": first.transaction_ref,
        "total_amount": f"{sum((item.course_fee or Decimal('0.00')) for item in group_records):.2f}",
        "courses": [
            {"code": item.course.code, "title": item.course.title, "fee": f"{item.course_fee:.2f}"}
            for item in group_records
        ],
        "payment_slip_filename": first.payment_slip_filename,
    }


@finance_bp.route("/")
@login_required
@roles_required("admin")
def overview():
    class_name = (request.args.get('class_name') or 'all').strip()
    invoices_query = Invoice.query.join(StudentProfile)
    if class_name != 'all':
        invoices_query = invoices_query.filter(StudentProfile.class_name == class_name)
    invoices = invoices_query.order_by(Invoice.due_date.asc(), Invoice.created_at.desc()).all()
    requests = CourseRequest.query.order_by(CourseRequest.created_at.desc()).all()
    grouped_requests = _group_requests(requests)
    total_due = sum(float(invoice.amount or 0) for invoice in invoices if invoice.status != "paid")
    total_paid = sum(float(invoice.amount or 0) for invoice in invoices if invoice.status == "paid")
    pending_requests = sum(1 for group in grouped_requests if group["status"] in {"awaiting_payment", "pending"})
    invoice_status_counts = {
        'paid': sum(1 for invoice in invoices if invoice.status == 'paid'),
        'unpaid': sum(1 for invoice in invoices if invoice.status == 'unpaid'),
        'overdue': sum(1 for invoice in invoices if invoice.status == 'overdue'),
        'partial': sum(1 for invoice in invoices if invoice.status == 'partial'),
    }
    return render_template(
        "finance/list.html",
        invoices=invoices,
        total_due=total_due,
        total_paid=total_paid,
        grouped_requests=grouped_requests[:10],
        pending_requests=pending_requests,
        invoice_status_counts=invoice_status_counts,
        class_name=class_name,
        class_options=sorted({student.class_name for student in StudentProfile.query.all()}),
    )


@finance_bp.route("/portal")
@login_required
@roles_required("student")
def portal():
    if current_user.student_profile:
        user_requests = CourseRequest.query.filter(
            (CourseRequest.requester_user_id == current_user.id)
            | (CourseRequest.student_id == current_user.student_profile.id)
        ).order_by(CourseRequest.created_at.desc()).all()
    else:
        user_requests = CourseRequest.query.filter_by(requester_user_id=current_user.id).order_by(CourseRequest.created_at.desc()).all()

    grouped_requests = _group_requests(user_requests)
    primary_student = current_user.student_profile
    available_courses = _available_courses_for_student(primary_student)
    total_pending_amount = sum(float(group["total"]) for group in grouped_requests if group["status"] in {"awaiting_payment", "pending"})

    return render_template(
        "finance/portal.html",
        linked_students=_accessible_students_for_user(current_user),
        available_courses=available_courses,
        grouped_requests=grouped_requests,
        total_pending_amount=total_pending_amount,
    )


@finance_bp.route('/portal/<request_group>/pay')
@login_required
@roles_required('student')
def payment_checkout(request_group):
    records = CourseRequest.query.filter_by(request_group=request_group, requester_user_id=current_user.id).order_by(CourseRequest.created_at.asc()).all()
    if not records:
        flash('Payment request group not found.', 'danger')
        return redirect(url_for('finance.portal'))

    grouped = _group_requests(records)
    group = grouped[0]
    selected_provider = (request.args.get('provider') or '').strip().lower()
    provider_meta = None
    if selected_provider in {'bkash', 'nagad', 'card', 'bank'}:
        provider_meta = payment_service.create_payment(selected_provider, {
            'request_group': request_group,
            'amount': f"{group['total']:.2f}",
            'requested_for_name': group['requested_for_name'],
            'requested_class': group['requested_class'],
        })
    return render_template('finance/checkout.html', group=group, selected_provider=selected_provider, provider_meta=provider_meta)


@finance_bp.post('/portal/create-request')
@login_required
@roles_required('student')
def create_course_request():
    course_ids = [int(course_id) for course_id in request.form.getlist('course_ids') if str(course_id).isdigit()]
    requested_for_name = (request.form.get('requested_for_name') or '').strip() or current_user.full_name
    requested_class = (request.form.get('requested_class') or '').strip() or (current_user.student_profile.class_name if current_user.student_profile else 'Not yet assigned')
    if not course_ids:
        flash('Please choose at least one course.', 'warning')
        return redirect(url_for('finance.portal'))

    student = current_user.student_profile
    courses = Course.query.filter(Course.id.in_(course_ids), Course.is_open_for_enrollment.is_(True)).all()
    if not courses:
        flash('Selected courses are not available for enrollment.', 'danger')
        return redirect(url_for('finance.portal'))

    existing_open = set(
        row.course_id for row in CourseRequest.query.filter(
            CourseRequest.requester_user_id == current_user.id,
            CourseRequest.status.in_(['awaiting_payment', 'pending', 'approved'])
        ).all()
    )
    selected = [course for course in courses if course.id not in existing_open]
    if not selected:
        flash('These courses already have an open or completed request.', 'warning')
        return redirect(url_for('finance.portal'))

    request_group = f"REQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{current_user.id}"
    for course in selected:
        db.session.add(CourseRequest(
            request_group=request_group,
            requester=current_user,
            student=student,
            course=course,
            course_fee=course.course_fee or 0,
            payment_provider='pending',
            payment_method='awaiting-payment',
            transaction_ref=request_group,
            payer_mobile=current_user.phone,
            status='awaiting_payment',
            requested_for_name=requested_for_name,
            requested_class=requested_class,
            admin_note='Course selection received. Waiting for student payment proof submission.',
        ))
    db.session.commit()
    flash('Course request created successfully. Please choose a payment gateway and complete the payment.', 'success')
    return redirect(url_for('finance.payment_checkout', request_group=request_group))


@finance_bp.post('/portal/<request_group>/submit-payment')
@login_required
@roles_required('student')
def submit_payment_proof(request_group):
    records = CourseRequest.query.filter_by(request_group=request_group, requester_user_id=current_user.id).all()
    if not records:
        flash('Payment request group not found.', 'danger')
        return redirect(url_for('finance.portal'))
    if any(record.status == 'approved' for record in records):
        flash('This request has already been approved.', 'info')
        return redirect(url_for('finance.portal'))

    payment_provider = (request.form.get('payment_provider') or '').strip().lower()
    payment_method = (request.form.get('payment_method') or '').strip()
    transaction_ref = (request.form.get('transaction_ref') or '').strip()
    payer_mobile = (request.form.get('payer_mobile') or '').strip()
    payment_slip = request.files.get('payment_slip')

    if not payment_provider or not payment_method or not transaction_ref:
        flash('Please provide payment provider, method, and transaction reference.', 'warning')
        return redirect(url_for('finance.portal'))
    if not payment_slip or not payment_slip.filename:
        flash('Please upload the payment slip as a PDF file.', 'warning')
        return redirect(url_for('finance.portal'))

    try:
        stored_slip_name, original_slip_name = _save_payment_slip(payment_slip, request_group)
    except ValueError as exc:
        flash(str(exc), 'danger')
        return redirect(url_for('finance.portal'))

    for record in records:
        record.payment_provider = payment_provider
        record.payment_method = payment_method
        record.transaction_ref = transaction_ref
        record.payer_mobile = payer_mobile or current_user.phone
        record.payment_slip_path = stored_slip_name
        record.payment_slip_filename = original_slip_name
        record.payment_slip_uploaded_at = datetime.utcnow()
        record.status = 'pending'
        record.admin_note = 'Payment proof submitted. Awaiting Aureline Admin verification within 24 hours.'
    db.session.commit()

    payload = _build_group_payload(records)
    attachment_path = os.path.join(_payment_slip_directory(), stored_slip_name)
    send_admin_payment_notifications(payload, attachment_path=attachment_path, attachment_name=original_slip_name)
    requester_email_result = send_requester_payment_copy(payload, attachment_path=attachment_path, attachment_name=original_slip_name)
    if requester_email_result.get('ok'):
        flash('Payment proof submitted successfully. A PDF copy has also been sent to your email address.', 'success')
    else:
        flash('Payment proof submitted successfully. Email copy could not be sent because mail settings are not configured yet.', 'warning')
    return redirect(url_for('finance.payment_checkout', request_group=request_group))


@finance_bp.route("/requests/<request_group>/slip")
@login_required
def download_payment_slip(request_group):
    records = CourseRequest.query.filter_by(request_group=request_group).all()
    if not records:
        abort(404)
    record = records[0]
    if current_user.role != "admin" and record.requester_user_id != current_user.id:
        abort(403)
    if not record.payment_slip_path:
        abort(404)
    return send_from_directory(
        _payment_slip_directory(),
        record.payment_slip_path,
        as_attachment=True,
        download_name=record.payment_slip_filename or record.payment_slip_path,
        mimetype="application/pdf",
    )


@finance_bp.route("/requests")
@login_required
@roles_required("admin")
def course_requests_admin():
    status = (request.args.get("status") or "all").strip().lower()
    query = CourseRequest.query.order_by(CourseRequest.created_at.desc())
    if status in {"awaiting_payment", "pending", "approved", "rejected"}:
        query = query.filter_by(status=status)
    grouped_requests = _group_requests(query.all())
    return render_template("finance/requests.html", grouped_requests=grouped_requests, status=status)


@finance_bp.post("/requests/<request_group>/approve")
@login_required
@roles_required("admin")
def approve_course_request_group(request_group):
    admin_note = (request.form.get("admin_note") or "").strip()
    records = CourseRequest.query.filter_by(request_group=request_group).all()
    if not records:
        flash("Payment request group not found.", "danger")
        return redirect(url_for("finance.course_requests_admin"))
    if any(record.status == 'awaiting_payment' for record in records):
        flash('This request is still waiting for payment proof from the student.', 'warning')
        return redirect(url_for('finance.course_requests_admin'))

    approved_count = 0
    billing_month = datetime.utcnow().strftime("%Y-%m")
    for record in records:
        if record.status == "approved":
            continue
        record.status = "approved"
        record.reviewed_by = current_user
        record.reviewed_at = datetime.utcnow()
        record.admin_note = admin_note or "Approved by Aureline Admin"
        approved_count += 1
        if record.student_id:
            existing_invoice = Invoice.query.filter_by(
                student_id=record.student_id,
                transaction_ref=record.transaction_ref,
                amount=record.course_fee,
            ).first()
            if not existing_invoice:
                db.session.add(Invoice(
                    invoice_no=_next_invoice_no(),
                    student_id=record.student_id,
                    course_id=record.course_id,
                    amount=record.course_fee,
                    due_date=date.today(),
                    billing_month=billing_month,
                    status="paid",
                    payment_provider=record.payment_provider,
                    payment_method=record.payment_method,
                    transaction_ref=record.transaction_ref,
                    paid_on=date.today(),
                    notes=f"Monthly subject fee approved for {record.course.code} via request {record.request_group}.",
                ))
            record.student.fee_status = "paid"
            record.enrollment_status = 'active'

    db.session.commit()
    flash(f"Approved {approved_count} course payment item(s).", "success")
    return redirect(url_for("finance.course_requests_admin"))


@finance_bp.post("/requests/<request_group>/reject")
@login_required
@roles_required("admin")
def reject_course_request_group(request_group):
    admin_note = (request.form.get("admin_note") or "").strip() or "Please verify payment and resubmit."
    records = CourseRequest.query.filter_by(request_group=request_group).all()
    if not records:
        flash("Payment request group not found.", "danger")
        return redirect(url_for("finance.course_requests_admin"))

    for record in records:
        record.status = "rejected"
        record.reviewed_by = current_user
        record.reviewed_at = datetime.utcnow()
        record.admin_note = admin_note

    db.session.commit()
    flash("Rejected the selected course payment request group.", "warning")
    return redirect(url_for("finance.course_requests_admin"))


@finance_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_invoice():
    form = InvoiceForm()
    form.student_id.choices = _student_choices()
    form.course_id.choices = _course_choices()
    if form.validate_on_submit():
        if _invoice_taken(form.invoice_no.data):
            form.invoice_no.errors.append("Invoice number already exists.")
        else:
            invoice = Invoice()
            _populate(invoice, form)
            db.session.add(invoice)
            db.session.commit()
            flash("Invoice created successfully.", "success")
            return redirect(url_for("finance.overview"))
    return render_template("finance/form.html", form=form, title="Create Invoice", submit_label="Create Invoice")


@finance_bp.route("/<int:invoice_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    form = InvoiceForm(obj=invoice)
    form.student_id.choices = _student_choices()
    form.course_id.choices = _course_choices()
    if request.method == "GET":
        form.student_id.data = invoice.student_id
        form.course_id.data = invoice.course_id or 0
    if form.validate_on_submit():
        if _invoice_taken(form.invoice_no.data, invoice.id):
            form.invoice_no.errors.append("Invoice number already exists.")
        else:
            _populate(invoice, form)
            db.session.commit()
            flash("Invoice updated successfully.", "success")
            return redirect(url_for("finance.overview"))
    return render_template("finance/form.html", form=form, title="Edit Invoice", submit_label="Update Invoice")


@finance_bp.route("/<int:invoice_id>/pay", methods=["POST"])
@login_required
@roles_required("admin")
def mark_paid(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = "paid"
    invoice.paid_on = invoice.paid_on or date.today()
    db.session.commit()
    flash("Invoice marked as paid.", "success")
    return redirect(url_for("finance.overview"))



@finance_bp.post("/<int:invoice_id>/delete")
@login_required
@roles_required("admin")
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    flash("Invoice deleted successfully.", "success")
    return redirect(url_for("finance.overview"))
