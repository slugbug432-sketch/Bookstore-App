import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "books.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

books = [
    ("The Great Gatsby (1925 First Edition)", "F. Scott Fitzgerald", "1111111111", 3, 1200.00, "gatsby.jpg", "Like New", "Original 1925 first edition. Rare collectible."),
    ("To Kill a Mockingbird (Signed Copy)", "Harper Lee", "2222222222", 2, 950.00, "mockingbird.jpg", "Good", "Signed by Harper Lee. Light wear."),
    ("1984 (First Printing)", "George Orwell", "3333333333", 4, 800.00, "1984.jpg", "Good", "First printing edition. Highly collectible."),
    ("Moby Dick (Antique Edition)", "Herman Melville", "4444444444", 1, 1500.00, "mobydick.jpg", "Fair", "Antique copy with aged pages."),
    ("The Hobbit (1937 Replica)", "J.R.R. Tolkien", "5555555555", 5, 600.00, "hobbit.jpg", "Like New", "Replica of original 1937 edition."),
    ("Pride and Prejudice (Collector's Edition)", "Jane Austen", "6666666666", 3, 450.00, "pride.jpg", "New", "Hardcover collector's edition."),
    ("Dracula (1897 Reprint Rare)", "Bram Stoker", "7777777777", 2, 700.00, "dracula.jpg", "Good", "Rare reprint of original 1897 edition.")
]

for book in books:
    cursor.execute("""
        INSERT OR IGNOREINTO books
        (title, author, isbn, quantity, price, image, condition, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, book)

conn.commit()
conn.close()

print("7 rare books added!")