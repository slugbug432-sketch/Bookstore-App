import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "noble_bookstore_secret_key"

DB_NAME = "books.db"
UPLOAD_FOLDER = "static/images"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return redirect(url_for("books"))


@app.route("/shop")
def shop():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return render_template("shop.html", books=books)


@app.route("/books")
def books():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return render_template("books.html", books=books)


@app.route("/book/<int:book_id>")
def book_detail(book_id):
    conn = get_db_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()

    if book is None:
        return "Book not found", 404

    return render_template("book_detail.html", book=book)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("dashboard"))

            return redirect(url_for("books"))

        return "Invalid username or password"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if session.get("role") != "admin":
        return "Access Denied"

    return redirect(url_for("books"))


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if session.get("role") != "admin":
        return "Access Denied"

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        quantity = request.form["quantity"]
        price = request.form["price"]
        condition = request.form["condition"]
        description = request.form["description"]

        filename = "default-book.png"

        image_file = request.files.get("image")

        if image_file and image_file.filename != "":
            if allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                image_file.save(image_path)

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO books
            (title, author, isbn, quantity, price, image, condition, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            author,
            isbn,
            quantity,
            price,
            filename,
            condition,
            description
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_book.html")


@app.route("/delete_book/<int:book_id>")
def delete_book(book_id):
    if session.get("role") != "admin":
        return "Access Denied"

    conn = get_db_connection()
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if session.get("role") != "admin":
        return "Access Denied"

    conn = get_db_connection()

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        conn.execute("""
            UPDATE books
            SET title = ?, author = ?, isbn = ?, quantity = ?, price = ?
            WHERE id = ?
        """, (title, author, isbn, quantity, price, book_id))
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()

    if book is None:
        return "Book not found", 404

    return render_template("edit_book.html", book=book)


if __name__ == "__main__":
    app.run(debug=True)