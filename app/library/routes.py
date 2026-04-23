from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from app.decorators import roles_required
from app.extensions import db
from app.forms import LibraryBookForm
from app.models import LibraryBook

library_bp = Blueprint("library", __name__, url_prefix="/library")


def _isbn_taken(isbn, current_id=None):
    if not isbn:
        return False
    query = LibraryBook.query.filter(LibraryBook.isbn == isbn.strip())
    if current_id:
        query = query.filter(LibraryBook.id != current_id)
    return db.session.query(query.exists()).scalar()


def _populate(book, form):
    book.title = form.title.data.strip()
    book.author = form.author.data.strip()
    book.isbn = form.isbn.data.strip() if form.isbn.data else None
    book.category = form.category.data.strip() if form.category.data else None
    book.shelf = form.shelf.data.strip() if form.shelf.data else None
    book.published_year = int(form.published_year.data) if form.published_year.data else None
    book.description = form.description.data.strip() if form.description.data else None
    book.copies_total = int(form.copies_total.data)
    book.copies_available = int(form.copies_available.data)


@library_bp.route("/")
@login_required
@roles_required("admin", "teacher", "student", "parent")
def catalog():
    books = LibraryBook.query.order_by(LibraryBook.title.asc()).all()
    return render_template("library/list.html", books=books)


@library_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_book():
    form = LibraryBookForm()
    if form.validate_on_submit():
        if _isbn_taken(form.isbn.data):
            form.isbn.errors.append("ISBN already exists.")
        else:
            book = LibraryBook()
            _populate(book, form)
            db.session.add(book)
            db.session.commit()
            flash("Book created successfully.", "success")
            return redirect(url_for("library.catalog"))
    return render_template("library/form.html", form=form, title="Add Book", submit_label="Create Book")


@library_bp.route("/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_book(book_id):
    book = LibraryBook.query.get_or_404(book_id)
    form = LibraryBookForm(obj=book)
    if request.method == "GET":
        form.published_year.data = str(book.published_year) if book.published_year else ""
        form.copies_total.data = str(book.copies_total)
        form.copies_available.data = str(book.copies_available)
    if form.validate_on_submit():
        if _isbn_taken(form.isbn.data, book.id):
            form.isbn.errors.append("ISBN already exists.")
        else:
            _populate(book, form)
            db.session.commit()
            flash("Book updated successfully.", "success")
            return redirect(url_for("library.catalog"))
    return render_template("library/form.html", form=form, title="Edit Book", submit_label="Update Book")


@library_bp.route("/<int:book_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_book(book_id):
    book = LibraryBook.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully.", "warning")
    return redirect(url_for("library.catalog"))
