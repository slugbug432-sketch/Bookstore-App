import sqlite3

DB_NAME = "books.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # BOOKS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE,
        quantity INTEGER DEFAULT 0,
        price REAL DEFAULT 0.00,
        image TEXT DEFAULT 'default-book.png',
        condition TEXT DEFAULT 'Good',
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # USERS TABLE WITH ROLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    conn.commit()
    conn.close()


def create_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    users = [
        ("EBarreno01", "team123", "admin"),
        ("JOspina02", "team123", "admin"),
        ("ROwens03", "team123", "admin"),
        ("KPeekSM", "team123", "admin"),
        ("FAlmarasiFadi01", "team123", "user")
    ]

    for username, password, role in users:
        try:
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            """, (username, password, role))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


def update_existing_books_table():
    """
    Adds new columns if books.db already exists.
    This prevents errors if the table was created before
    image, condition, price, and description were added.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    columns_to_add = [
        ("price", "REAL DEFAULT 0.00"),
        ("image", "TEXT DEFAULT 'default-book.png'"),
        ("condition", "TEXT DEFAULT 'Good'"),
        ("description", "TEXT")
    ]

    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(
                f"ALTER TABLE books ADD COLUMN {column_name} {column_type}"
            )
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    update_existing_books_table()
    create_users()
    print("Database created/updated successfully.")