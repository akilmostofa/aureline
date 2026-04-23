from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required
from app.decorators import roles_required
from app.extensions import db
from app.forms import NoticeForm
from app.models import Notice

communication_bp = Blueprint("communication", __name__, url_prefix="/communication")


@communication_bp.route("/")
@login_required
@roles_required("admin", "teacher", "student", "parent")
def notices():
    notices = Notice.query.order_by(Notice.is_pinned.desc(), Notice.published_on.desc(), Notice.id.desc()).all()
    return render_template("communication/list.html", notices=notices)


@communication_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_notice():
    form = NoticeForm()
    if form.validate_on_submit():
        notice = Notice(
            title=form.title.data.strip(),
            audience=form.audience.data,
            message=form.message.data.strip(),
            published_on=form.published_on.data,
            is_pinned=form.is_pinned.data,
        )
        db.session.add(notice)
        db.session.commit()
        flash("Notice created successfully.", "success")
        return redirect(url_for("communication.notices"))
    return render_template("communication/form.html", form=form, title="Create Notice", submit_label="Create Notice")


@communication_bp.route("/<int:notice_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    form = NoticeForm(obj=notice)
    if form.validate_on_submit():
        notice.title = form.title.data.strip()
        notice.audience = form.audience.data
        notice.message = form.message.data.strip()
        notice.published_on = form.published_on.data
        notice.is_pinned = form.is_pinned.data
        db.session.commit()
        flash("Notice updated successfully.", "success")
        return redirect(url_for("communication.notices"))
    return render_template("communication/form.html", form=form, title="Edit Notice", submit_label="Update Notice")


@communication_bp.route("/<int:notice_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    db.session.delete(notice)
    db.session.commit()
    flash("Notice deleted successfully.", "warning")
    return redirect(url_for("communication.notices"))
