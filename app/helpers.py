import os
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename

from .models import StudentProfile, TeacherProfile


def generate_student_id():
    next_num = StudentProfile.query.count() + 1
    candidate = f"AA-STD-{next_num:04d}"
    while StudentProfile.query.filter_by(admission_no=candidate).first():
        next_num += 1
        candidate = f"AA-STD-{next_num:04d}"
    return candidate


def generate_teacher_id():
    next_num = TeacherProfile.query.count() + 1
    candidate = f"AA-TCH-{next_num:04d}"
    while TeacherProfile.query.filter_by(employee_id=candidate).first():
        next_num += 1
        candidate = f"AA-TCH-{next_num:04d}"
    return candidate


def profile_upload_directory():
    return os.path.join(current_app.instance_path, current_app.config["PROFILE_UPLOAD_FOLDER"])


def save_profile_image(file_storage, prefix):
    if not file_storage or not file_storage.filename:
        return None, None
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in {'jpg', 'jpeg', 'png', 'webp'}:
        raise ValueError('Profile image must be JPG, PNG, or WEBP.')
    stored_name = f"{prefix}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.{ext}"
    absolute_path = os.path.join(profile_upload_directory(), stored_name)
    file_storage.save(absolute_path)
    return stored_name, filename
