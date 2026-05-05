import sqlite3

conn = sqlite3.connect("libraries.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS libraries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    name TEXT
)
""")

data = [
    ("usak", "مكتبة أوشاك المركزية"),
    ("usak", "مكتبة الجامعة"),
    ("istanbul", "مكتبة إسطنبول العامة"),
    ("istanbul", "مكتبة تقسيم")
]

cur.executemany("INSERT INTO libraries (city, name) VALUES (?, ?)", data)

conn.commit()
conn.close()

print("DB جاهزة")
