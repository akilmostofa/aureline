from datetime import datetime

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.decorators import roles_required
from app.extensions import db
from app.models import Course, RecordedClassVideo
from .zoom_service import ZoomService

integrations_bp = Blueprint("integrations", __name__, url_prefix="/integrations")


@integrations_bp.route("/zoom/auth-url")
@login_required
@roles_required("admin", "teacher")
def zoom_auth_url():
    return jsonify({"auth_url": ZoomService(current_app.config).authorization_url()})


@integrations_bp.route("/zoom/callback")
def zoom_callback():
    code = request.args.get("code")
    return jsonify(ZoomService(current_app.config).exchange_code_for_token(code=code))


@integrations_bp.route('/recordings')
@login_required
def recordings_library():
    query = RecordedClassVideo.query.join(Course)
    class_filter = (request.args.get('class_name') or '').strip()
    if current_user.role == 'student' and current_user.student_profile:
        query = query.filter(RecordedClassVideo.class_name == current_user.student_profile.class_name)
    elif current_user.role == 'teacher' and current_user.teacher_profile:
        query = query.filter(Course.teacher_id == current_user.teacher_profile.id)
    if class_filter:
        query = query.filter(RecordedClassVideo.class_name == class_filter)
    recordings = query.order_by(RecordedClassVideo.recording_date.desc(), RecordedClassVideo.created_at.desc()).all()
    classes = [row[0] for row in db.session.query(RecordedClassVideo.class_name).distinct().order_by(RecordedClassVideo.class_name.asc()).all()]
    return render_template('integrations/recordings.html', recordings=recordings, classes=classes, class_filter=class_filter)


@integrations_bp.post('/zoom/recording-complete')
def zoom_recording_complete():
    payload = request.get_json(silent=True) or {}
    meeting = payload.get('payload', {}).get('object', {})
    meeting_id = str(meeting.get('id') or '')
    course = Course.query.filter_by(zoom_meeting_id=meeting_id).first()
    if not course:
        return jsonify({'ok': False, 'message': 'No matching course for meeting id'}), 404

    share_url = None
    recording_files = meeting.get('recording_files') or []
    if recording_files:
        share_url = recording_files[0].get('play_url') or recording_files[0].get('download_url')
    if not share_url:
        share_url = meeting.get('share_url')
    if not share_url:
        return jsonify({'ok': False, 'message': 'No recording URL found in payload'}), 400

    title = meeting.get('topic') or f"{course.title} Recording"
    start_time = meeting.get('start_time')
    recording_date = datetime.utcnow().date()
    if start_time:
        try:
            recording_date = datetime.fromisoformat(start_time.replace('Z', '+00:00')).date()
        except Exception:
            pass

    record = RecordedClassVideo.query.filter_by(zoom_meeting_id=meeting_id, title=title, video_url=share_url).first()
    if not record:
        record = RecordedClassVideo(course=course)
        db.session.add(record)
    record.title = title
    record.class_name = course.class_name
    record.subject_label = course.title
    record.zoom_meeting_id = meeting_id
    record.recording_date = recording_date
    record.video_url = share_url
    record.duration_minutes = int(meeting.get('duration') or 0) or None
    record.source = 'zoom'
    record.access_scope = 'class_only'
    record.notes = 'Auto-synced from Zoom recording completion webhook.'
    db.session.commit()
    return jsonify({'ok': True, 'message': 'Recording synced successfully'})
