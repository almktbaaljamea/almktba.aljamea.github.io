import sqlite3

conn = sqlite3.connect("books.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS books (
    book_name TEXT,
    publisher TEXT,
    library TEXT,
    city TEXT
)
""")

data = [
    ("Clean Code", "Prentice Hall", "مكتبة الجامعة", "Uşak"),
    ("Python Basics", "O'Reilly", "مكتبة إسطنبول العامة", "Istanbul"),
    ("Urban Planning", "Springer", "مكتبة تقسيم", "Istanbul")
]

cur.executemany("INSERT INTO books VALUES (?, ?, ?, ?)", data)

conn.commit()
conn.close()

print("DB READY")