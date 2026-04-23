from datetime import date, datetime, timedelta
from flask import current_app

from .extensions import db
from .helpers import generate_student_id, generate_teacher_id
from .models import Attendance, ClassTestResult, Course, CourseRequest, Invoice, LibraryBook, Notice, RecordedClassVideo, StudentProfile, TeacherProfile, User


def upsert_user(email, full_name, role, password, phone=None, is_active=True, approval_status="approved", registration_source="seeded_demo"):
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email)
        db.session.add(user)
    user.full_name = full_name
    user.role = role
    user.phone = phone
    user.is_active = is_active
    user.approval_status = approval_status
    user.registration_source = registration_source
    if approval_status == "approved" and not user.approved_at:
        user.approved_at = datetime.utcnow()
    if password:
        user.set_password(password)
    return user


def seed_demo_data():
    admin = upsert_user("admin@aureline.edu", "Aureline System Admin", "admin", "admin123", "+8801700000001")
    teacher_user = upsert_user("teacher@aureline.edu", "Md. Farhan Alam", "teacher", "teacher123", "+8801700000003")
    teacher2_user = upsert_user("teacher2@aureline.edu", "Shaila Islam", "teacher", "teacher123", "+8801700000005")
    student_user = upsert_user("student@aureline.edu", "Sadia Rahman", "student", "student123", "+8801700000004")
    student2_user = upsert_user("student2@aureline.edu", "Ayman Hossain", "student", "student123", "+8801700000006")
    pending_user = upsert_user("pending.student@aureline.edu", "Demo Pending Student", "student", "student123", "+8801700000008", is_active=False, approval_status="pending", registration_source="public_registration")

    db.session.flush()

    teacher = TeacherProfile.query.filter_by(user_id=teacher_user.id).first() or TeacherProfile(user=teacher_user, employee_id=generate_teacher_id())
    db.session.add(teacher)
    teacher.employee_id = teacher.employee_id or generate_teacher_id()
    teacher.department = "Science"
    teacher.subject_specialty = "Mathematics"
    teacher.qualification = "MSc in Mathematics"
    teacher.join_date = date.today() - timedelta(days=365)
    teacher.address = "Mirpur, Dhaka"

    teacher2 = TeacherProfile.query.filter_by(user_id=teacher2_user.id).first() or TeacherProfile(user=teacher2_user, employee_id=generate_teacher_id())
    db.session.add(teacher2)
    teacher2.employee_id = teacher2.employee_id or generate_teacher_id()
    teacher2.department = "Humanities"
    teacher2.subject_specialty = "English"
    teacher2.qualification = "MA in English"
    teacher2.join_date = date.today() - timedelta(days=180)
    teacher2.address = "Uttara, Dhaka"

    student = StudentProfile.query.filter_by(user_id=student_user.id).first() or StudentProfile(user=student_user, admission_no=generate_student_id())
    db.session.add(student)
    student.admission_no = student.admission_no or generate_student_id()
    student.class_name = "Grade 8"
    student.section = "A"
    student.guardian_name = "Nusrat Jahan"
    student.guardian_occupation = "Banker"
    student.guardian_phone = "+8801711111111"
    student.parent_email = "guardian@example.com"
    student.current_school_name = "Aureline Junior School"
    student.address = "Dhaka, Bangladesh"
    student.fee_status = "partial"
    student.progress_note = "Strong progress in mathematics and science."

    student2 = StudentProfile.query.filter_by(user_id=student2_user.id).first() or StudentProfile(user=student2_user, admission_no=generate_student_id())
    db.session.add(student2)
    student2.admission_no = student2.admission_no or generate_student_id()
    student2.class_name = "Grade 7"
    student2.section = "B"
    student2.guardian_name = "Rafiq Hossain"
    student2.guardian_occupation = "Engineer"
    student2.guardian_phone = "+8801722222222"
    student2.parent_email = "guardian2@example.com"
    student2.current_school_name = "City Scholars School"
    student2.address = "Chattogram, Bangladesh"
    student2.fee_status = "paid"
    student2.progress_note = "Needs additional mentoring in English composition."

    pending_profile = StudentProfile.query.filter_by(user_id=pending_user.id).first() or StudentProfile(user=pending_user, admission_no=generate_student_id())
    db.session.add(pending_profile)
    pending_profile.admission_no = pending_profile.admission_no or generate_student_id()
    pending_profile.class_name = "Pending Assignment"
    pending_profile.guardian_name = "Demo Guardian"
    pending_profile.guardian_occupation = "Teacher"
    pending_profile.guardian_phone = "+8801712345678"
    pending_profile.parent_email = pending_user.email
    pending_profile.current_school_name = "Future School"
    pending_profile.address = "Gazipur, Bangladesh"
    pending_profile.fee_status = "pending"
    pending_profile.progress_note = "Awaiting Aureline Admin approval."

    db.session.flush()

    math = Course.query.filter_by(code="MATH-08").first() or Course(code="MATH-08")
    db.session.add(math)
    math.title = "Mathematics for Grade 8"
    math.class_name = "Grade 8"
    math.teacher = teacher
    math.room = "Room 301"
    math.schedule_text = "Sun-Tue 10:00 AM"
    math.delivery_status = "running"
    math.description = "Core mathematics curriculum with algebra, geometry, and exams."
    math.course_fee = 12000
    math.is_open_for_enrollment = True
    math.zoom_meeting_id = "908001"

    eng = Course.query.filter_by(code="ENG-07").first() or Course(code="ENG-07")
    db.session.add(eng)
    eng.title = "English Literature"
    eng.class_name = "Grade 7"
    eng.teacher = teacher2
    eng.room = "Room 205"
    eng.schedule_text = "Mon-Wed 11:30 AM"
    eng.delivery_status = "running"
    eng.description = "Reading, writing, and speaking practice."
    eng.course_fee = 10000
    eng.is_open_for_enrollment = True
    eng.zoom_meeting_id = "908002"

    science = Course.query.filter_by(code="SCI-08").first() or Course(code="SCI-08")
    db.session.add(science)
    science.title = "General Science"
    science.class_name = "Grade 8"
    science.teacher = teacher
    science.room = "Lab 1"
    science.schedule_text = "Mon-Thu 9:00 AM"
    science.delivery_status = "running"
    science.description = "Science concepts, experiments, and lab safety."
    science.course_fee = 13000
    science.is_open_for_enrollment = True
    science.zoom_meeting_id = "908003"

    db.session.flush()

    for attended_on, status, notes in [
        (date.today(), 'present', 'Joined class and completed assignment.'),
        (date.today() - timedelta(days=1), 'present', 'Completed homework review.'),
        (date.today() - timedelta(days=2), 'late', 'Joined 5 minutes late.'),
    ]:
        attendance = Attendance.query.filter_by(student_id=student.id, course_id=math.id, attended_on=attended_on).first() or Attendance(student=student, course=math, attended_on=attended_on)
        db.session.add(attendance)
        attendance.status = status
        attendance.notes = notes

    attendance2 = Attendance.query.filter_by(student_id=student2.id, course_id=eng.id, attended_on=date.today()).first() or Attendance(student=student2, course=eng, attended_on=date.today())
    db.session.add(attendance2)
    attendance2.status = "late"
    attendance2.notes = "Arrived 10 minutes late."

    current_month = datetime.utcnow().strftime('%Y-%m')
    invoice1 = Invoice.query.filter_by(invoice_no="INV-2026-001").first() or Invoice(invoice_no="INV-2026-001", student=student)
    db.session.add(invoice1)
    invoice1.course = math
    invoice1.amount = 12000
    invoice1.billing_month = current_month
    invoice1.due_date = date.today() + timedelta(days=3)
    invoice1.status = "partial"
    invoice1.payment_provider = "bkash"
    invoice1.payment_method = "wallet"
    invoice1.transaction_ref = "BKASH-DEMO-001"
    invoice1.notes = "Monthly subject fee installment 1 received."

    invoice2 = Invoice.query.filter_by(invoice_no="INV-2026-002").first() or Invoice(invoice_no="INV-2026-002", student=student)
    db.session.add(invoice2)
    invoice2.course = science
    invoice2.amount = 13000
    invoice2.billing_month = current_month
    invoice2.due_date = date.today() - timedelta(days=1)
    invoice2.status = "unpaid"
    invoice2.notes = "Subject-wise monthly fee waiting for payment confirmation."

    invoice3 = Invoice.query.filter_by(invoice_no="INV-2026-003").first() or Invoice(invoice_no="INV-2026-003", student=student2)
    db.session.add(invoice3)
    invoice3.course = eng
    invoice3.amount = 10000
    invoice3.billing_month = current_month
    invoice3.due_date = date.today() + timedelta(days=5)
    invoice3.status = "paid"
    invoice3.payment_provider = "card"
    invoice3.payment_method = "Visa"
    invoice3.transaction_ref = "CARD-DEMO-002"
    invoice3.paid_on = date.today() - timedelta(days=1)
    invoice3.notes = "Paid in full."

    request_group = "REQ-DEMO-001"
    request_item = CourseRequest.query.filter_by(request_group=request_group, course_id=science.id).first() or CourseRequest(request_group=request_group, requester=student_user, student=student, course=science)
    db.session.add(request_item)
    request_item.course_fee = science.course_fee
    request_item.payment_provider = "bkash"
    request_item.payment_method = "wallet"
    request_item.transaction_ref = "BKASH-REQ-003"
    request_item.payer_mobile = student_user.phone
    request_item.status = "pending"
    request_item.requested_for_name = student.user.full_name
    request_item.requested_class = student.class_name
    request_item.payment_slip_filename = request_item.payment_slip_filename or "demo-slip.pdf"
    request_item.payment_slip_path = request_item.payment_slip_path or "demo-slip.pdf"
    request_item.payment_slip_uploaded_at = request_item.payment_slip_uploaded_at or datetime.utcnow()

    approved_math = CourseRequest.query.filter_by(request_group="REQ-APPROVED-MATH", course_id=math.id, student_id=student.id).first() or CourseRequest(request_group="REQ-APPROVED-MATH", requester=student_user, student=student, course=math)
    db.session.add(approved_math)
    approved_math.course_fee = math.course_fee
    approved_math.payment_provider = "bkash"
    approved_math.payment_method = "wallet"
    approved_math.transaction_ref = "BKASH-MATH-APPROVED"
    approved_math.payer_mobile = student_user.phone
    approved_math.status = "approved"
    approved_math.enrollment_status = "active"
    approved_math.requested_for_name = student.user.full_name
    approved_math.requested_class = student.class_name

    approved_science = CourseRequest.query.filter_by(request_group="REQ-APPROVED-SCI", course_id=science.id, student_id=student.id).first() or CourseRequest(request_group="REQ-APPROVED-SCI", requester=student_user, student=student, course=science)
    db.session.add(approved_science)
    approved_science.course_fee = science.course_fee
    approved_science.payment_provider = "bkash"
    approved_science.payment_method = "wallet"
    approved_science.transaction_ref = "BKASH-SCI-APPROVED"
    approved_science.payer_mobile = student_user.phone
    approved_science.status = "approved"
    approved_science.enrollment_status = "suspended"
    approved_science.requested_for_name = student.user.full_name
    approved_science.requested_class = student.class_name

    approved_eng = CourseRequest.query.filter_by(request_group="REQ-APPROVED-ENG", course_id=eng.id, student_id=student2.id).first() or CourseRequest(request_group="REQ-APPROVED-ENG", requester=student2_user, student=student2, course=eng)
    db.session.add(approved_eng)
    approved_eng.course_fee = eng.course_fee
    approved_eng.payment_provider = "card"
    approved_eng.payment_method = "visa"
    approved_eng.transaction_ref = "CARD-ENG-APPROVED"
    approved_eng.payer_mobile = student2_user.phone
    approved_eng.status = "approved"
    approved_eng.enrollment_status = "active"
    approved_eng.requested_for_name = student2.user.full_name
    approved_eng.requested_class = student2.class_name

    for title, obtained, total, grade, exam_date, course_obj in [
        ('Weekly Quiz 1', 18, 20, 'A+', date.today() - timedelta(days=3), math),
        ('Class Test - Algebra', 42, 50, 'A', date.today() - timedelta(days=10), math),
        ('Science Chapter Test', 36, 50, 'B', date.today() - timedelta(days=6), science),
    ]:
        result = ClassTestResult.query.filter_by(student_id=student.id, course_id=course_obj.id, test_title=title).first() or ClassTestResult(student=student, course=course_obj, teacher=teacher, test_title=title)
        db.session.add(result)
        result.obtained_marks = obtained
        result.total_marks = total
        result.grade = grade
        result.exam_date = exam_date
        result.remarks = 'Demo result entry for student dashboard.'

    recording = RecordedClassVideo.query.filter_by(course=math, title="Mathematics for Grade 8 - Algebra Revision").first() or RecordedClassVideo(course=math)
    db.session.add(recording)
    recording.title = "Mathematics for Grade 8 - Algebra Revision"
    recording.class_name = math.class_name
    recording.subject_label = math.title
    recording.zoom_meeting_id = math.zoom_meeting_id
    recording.recording_date = date.today() - timedelta(days=2)
    recording.video_url = "https://example.com/recordings/math-grade8-algebra"
    recording.duration_minutes = 55
    recording.source = "zoom"
    recording.access_scope = "class_only"
    recording.notes = "Demo recording library entry. Replace with live Zoom recording URL in production."

    books = [
        {"title": "Higher Math Essentials", "author": "A. Karim", "isbn": "9780000000011", "category": "Mathematics", "shelf": "M-12", "published_year": 2021, "copies_total": 10, "copies_available": 6},
        {"title": "English Writing Workshop", "author": "S. Ahmed", "isbn": "9780000000012", "category": "English", "shelf": "E-03", "published_year": 2020, "copies_total": 8, "copies_available": 8},
    ]
    for item in books:
        book = LibraryBook.query.filter_by(isbn=item["isbn"]).first() or LibraryBook(isbn=item["isbn"])
        db.session.add(book)
        for key, value in item.items():
            setattr(book, key, value)
        book.description = f"Aureline Academy library copy for {item['category']}."

    notice = Notice.query.filter_by(title="Orientation & Fee Reminder").first() or Notice(title="Orientation & Fee Reminder")
    db.session.add(notice)
    notice.audience = "all"
    notice.message = "New term orientation is on Monday. Please clear subject-wise fee dues before the first class."
    notice.published_on = date.today()
    notice.is_pinned = True

    db.session.commit()
    current_app.logger.info("Demo data seeded successfully.")
