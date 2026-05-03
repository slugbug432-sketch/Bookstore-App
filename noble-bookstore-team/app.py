from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# =========================
# CONFIG
# =========================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# MODELS (SAAS CLEAN)
# =========================
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"))
    quantity = db.Column(db.Integer)
    total = db.Column(db.Float)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # admin / staff / viewer

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(120))

# =========================
# ROLE SYSTEM (FIXED)
# =========================
def role_required(roles):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login"))

            if session.get("role") not in roles:
                flash("Unauthorized access", "danger")
                return redirect(url_for("dashboard"))

            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


# =========================
# AUTH
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("dashboard"))

        flash("Invalid login", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# DASHBOARD (SAAS ANALYTICS CORE)
# =========================
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    total_books = Book.query.count()
    total_sales = db.session.query(db.func.sum(Sale.total)).scalar() or 0
    low_stock = Book.query.filter(Book.quantity <= 5).count()

    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        total_books=total_books,
        total_sales=total_sales,
        low_stock=low_stock
    )


# =========================
# CHART API (FOR CHART.JS)
# =========================
@app.route("/api/sales-chart")
def sales_chart():
    data = db.session.query(
        db.func.strftime("%Y-%m-%d", Sale.date),
        db.func.sum(Sale.total)
    ).group_by(db.func.strftime("%Y-%m-%d", Sale.date)).all()

    return jsonify({
        "labels": [d[0] for d in data],
        "values": [d[1] for d in data]
    })


# =========================
# INVENTORY
# =========================
@app.route("/inventory")
def inventory():
    books = Book.query.all()
    return render_template("books.html", books=books)


@app.route("/add_book", methods=["GET", "POST"])
@role_required(["admin"])
def add_book():
    if request.method == "POST":
        book = Book(
            title=request.form["title"],
            author=request.form["author"],
            isbn=request.form["isbn"],
            price=float(request.form["price"]),
            quantity=int(request.form["quantity"])
        )

        db.session.add(book)
        db.session.commit()

        flash("Book added", "success")
        return redirect(url_for("inventory"))

    return render_template("add_book.html")

@app.route("/purchase_orders")
def purchase_orders():
    return render_template("purchase_orders.html")

@app.route("/suppliers")
def suppliers():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("suppliers.html", suppliers=Supplier.query.all())
    all_suppliers = Supplier.query.all()
    return render_template("suppliers.html", suppliers=all_suppliers)

@app.route("/add_supplier", methods=["POST"])
def add_supplier():
    if "username" not in session:
        return redirect(url_for("login"))

    supplier = Supplier(
        name=request.form["name"],
        contact=request.form["contact"]
    )

    db.session.add(supplier)
    db.session.commit()

    flash("Supplier added", "success")
    return redirect(url_for("suppliers"))

@app.route("/delete_book/<int:id>")
@role_required(["admin"])
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()

    flash("Book deleted", "success")
    return redirect(url_for("inventory"))


# =========================
# CHECKOUT
# =========================
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    books = Book.query.all()

    if request.method == "POST":
        book = Book.query.get(int(request.form["book_id"]))
        qty = int(request.form["quantity"])

        if book.quantity < qty:
            flash("Not enough stock", "danger")
            return redirect(url_for("checkout"))

        total = book.price * qty
        book.quantity -= qty

        sale = Sale(book_id=book.id, quantity=qty, total=total)
        db.session.add(sale)
        db.session.commit()

        flash("Sale completed", "success")
        return redirect(url_for("dashboard"))

    return render_template("checkout.html", books=books)


# =========================
# SALES HISTORY
# =========================
@app.route("/sales_history")
def sales_history():
    sales = Sale.query.order_by(Sale.date.desc()).all()
    return render_template("sales_history.html", sales=sales)


# =========================
# LOW STOCK
# =========================
@app.route("/low_stock")
def low_stock():
    books = Book.query.filter(Book.quantity <= 5).all()
    return render_template("low_stock.html", books=books)


# =========================
# PUBLIC BOOKSTORE
# =========================
@app.route("/shop")
def shop():
    books = Book.query.filter(Book.quantity > 0).all()
    return render_template("shop.html", books=books)


# =========================
# INIT DB
# =========================
with app.app_context():
    db.create_all()

    # Add sample books if none exist
    try:
        book_count = Book.query.count()
        has_books = book_count > 0
    except:
        has_books = False
    
    if not has_books:
        sample_books = [
            Book(title="The Great Gatsby", author="F. Scott Fitzgerald", isbn="978-0-7432-7356-5", price=12.99, quantity=25),
            Book(title="To Kill a Mockingbird", author="Harper Lee", isbn="978-0-06-112008-4", price=14.99, quantity=30),
            Book(title="1984", author="George Orwell", isbn="978-0-452-28423-4", price=11.99, quantity=20),
            Book(title="Pride and Prejudice", author="Jane Austen", isbn="978-0-14-143951-8", price=9.99, quantity=35),
            Book(title="The Catcher in the Rye", author="J.D. Salinger", isbn="978-0-316-76948-0", price=10.99, quantity=28),
            Book(title="Harry Potter and the Sorcerer's Stone", author="J.K. Rowling", isbn="978-0-590-35340-3", price=16.99, quantity=40),
            Book(title="The Lord of the Rings", author="J.R.R. Tolkien", isbn="978-0-544-00003-7", price=25.99, quantity=15),
            Book(title="Dune", author="Frank Herbert", isbn="978-0-441-17271-9", price=13.99, quantity=22),
        ]
        db.session.add_all(sample_books)
        db.session.commit()

    # Add sample users if none exist
    if User.query.count() == 0:
        sample_users = [
            User(username="admin", password="admin123", role="admin"),
            User(username="staff", password="staff123", role="staff"),
        ]
        db.session.add_all(sample_users)
        db.session.commit()


# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)