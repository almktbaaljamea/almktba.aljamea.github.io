import sqlite3
import requests
import time
import random
import os

DATABASE = "books.db"

# List of 50 Arabic book titles
book_titles = [
    "البداية والنهاية", "قواعد العشق الأربعون", "مقدمة ابن خلدون", "لا تحزن", "الرحيق المختوم",
    "ثلاثية غرناطة", "الأسود يليق بك", "عزازيل", "شيفرة بلال", "أولاد حارتنا",
    "الخيميائي", "مئة عام من العزلة", "رجال في الشمس", "في قلبي أنثى عبرية", "أنتخريستوس",
    "البؤساء", "الجريمة والعقاب", "يوتوبيا", "تراب الماس", "الفيل الأزرق",
    "أرض زيكولا", "ذاكرة الجسد", "الطنطورية", "عائد إلى حيفا", "ساق البامبو",
    "تفسير الجلالين", "صحيح البخاري", "رياض الصالحين", "شمس المعارف", "طوق الحمامة",
    "حي بن يقظان", "رسالة الغفران", "كليلة ودمنة", "ألف ليلة وليلة", "البخلاء",
    "العبقريات", "الأيام", "عبقرية محمد", "الإسلام بين الشرق والغرب", "دعاء الكروان",
    "موسم الهجرة إلى الشمال", "اللص والكلاب", "حديث الصباح والمساء", "عمارة يعقوبيان", "عطارد",
    "هيبتا", "سفينة نوح", "النبي", "الأرواح المتمردة", "الأجنحة المتكسرة"
]

libraries = ["مكتبة الشبكة العربية", "مكتبة الأسرة", "مكتبة دار السلام", "المكتبة الهاشمية", "مكتبة اقرأ"]
cities = ["إسطنبول", "غازي عنتاب", "أنطاكيا", "مرسين", "بورصة"]
publishers = ["دار الشروق", "الدار العربية للعلوم", "دار المعارف", "دار العلم للملايين", "دار الآداب"]

def get_book_cover(title):
    try:
        url = f"https://openlibrary.org/search.json?q={requests.utils.quote(title)}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if 'docs' in data and len(data['docs']) > 0:
            for doc in data['docs']:
                if 'cover_i' in doc:
                    return f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                # If no exact cover, check if there's an ISBN
                if 'isbn' in doc and len(doc['isbn']) > 0:
                    return f"https://covers.openlibrary.org/b/isbn/{doc['isbn'][0]}-L.jpg"
    except Exception as e:
        print(f"Error fetching cover for {title}: {e}")
    
    # Fallback to a placeholder if OpenLibrary fails or has no cover
    # We use Google Books search via Goodreads fallback locally? No, we just return empty string or a generated image.
    return ""

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT,
            city TEXT,
            library TEXT,
            price TEXT,
            publisher TEXT,
            cover_image TEXT,
            isbn TEXT
        )
    """)
    # Clear existing data
    cursor.execute("DELETE FROM books")
    
    books_added = 0
    print(f"Fetching covers and populating 50 books...")
    for title in book_titles:
        cover_url = get_book_cover(title)
        library = random.choice(libraries)
        city = random.choice(cities)
        publisher = random.choice(publishers)
        price = str(random.randint(50, 400))
        isbn = f"978-{random.randint(100000000, 999999999)}"
        
        # If openlibrary fails, provide a fallback image URL that is generic but works
        if not cover_url:
            cover_url = f"https://placehold.co/400x600/C19A6B/FFFFFF?text={requests.utils.quote(title)}"
        
        cursor.execute("""
            INSERT INTO books (book_name, city, library, price, publisher, cover_image, isbn)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, city, library, price, publisher, cover_url, isbn))
        
        books_added += 1
        print(f"Added: {title} ({books_added}/50)")
        time.sleep(0.5) # Sleep to avoid rate limiting
        
    conn.commit()
    conn.close()
    print("Database populated successfully!")

if __name__ == "__main__":
    init_db()
