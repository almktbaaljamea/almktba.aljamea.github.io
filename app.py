from flask import Flask, request, jsonify, render_template_string, redirect, send_file
import sqlite3
import pandas as pd
import os
import urllib.parse
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
import re
from difflib import SequenceMatcher
import io

app = Flask(__name__, static_folder='out', static_url_path='/')
# مسار قاعدة البيانات
DATABASE = os.path.join(os.path.dirname(__file__), "books.db")

# كلمة مرور لوحة التحكم (غيّرها كما تريد)
ADMIN_PASSWORD = "hasanbook2026"

# ========== تحويل تلقائي من Excel إلى SQLite عند أول تشغيل ==========
def init_db():
    if not os.path.exists(DATABASE):
        try:
            df = pd.read_excel("books.xlsx")
            df = df.fillna("")
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
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
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO books (book_name, city, library, price, publisher, cover_image, isbn)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("book_name", ""),
                    row.get("city", ""),
                    row.get("library", ""),
                    str(row.get("price", "")),
                    row.get("publisher", ""),
                    row.get("cover_image", ""),
                    str(row.get("isbn", ""))
                ))
            conn.commit()
            conn.close()
            print("✅ تم إنشاء books.db من books.xlsx بنجاح!")
        except Exception as e:
            print("❌ خطأ أثناء تحويل الإكسيل:", e)

# تشغيل التهيئة
init_db()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ========== البحث في قاعدة البيانات ==========
def search(query):
    conn = get_db()
    results = conn.execute(
        "SELECT * FROM books WHERE book_name LIKE ?",
        (f'%{query}%',)
    ).fetchall()
    conn.close()
    return [dict(row) for row in results]

# ========== نقطة النهاية الذكية لـ Goodreads ==========
@app.route("/get_goodreads_link")
def get_goodreads_link():
    book_name = request.args.get("q", "").strip()
    if not book_name:
        return jsonify({"error": "No query"}), 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    search_url = f"https://www.goodreads.com/search?q={requests.utils.quote(book_name)}"

    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return jsonify({"url": None, "message": "فشل الاتصال بـ Goodreads"})

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="tableList")
        if not table:
            return jsonify({"url": None, "message": "لم يتم العثور على نتائج"})

        rows = table.find_all("tr")
        best_match = None
        best_score = -1

        for row in rows:
            link_tag = row.find("a", class_="bookTitle")
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            if not href.startswith("http"):
                href = "https://www.goodreads.com" + href

            # استخراج التقييم وعدد المقيمين
            rating_span = None
            for span in row.find_all("span"):
                if "minirating" in span.get("class", []):
                    rating_span = span
                    break

            rating = 0.0
            ratings_count = 0
            if rating_span:
                text = rating_span.get_text()
                rating_match = re.search(r'(\d+\.?\d*)\s*avg', text)
                count_match = re.search(r'(\d[\d,]*)\s*ratings', text)
                if rating_match:
                    rating = float(rating_match.group(1))
                if count_match:
                    ratings_count = int(count_match.group(1).replace(',', ''))

            # حساب درجة المطابقة: تشابه النص + التقييم + عدد المقيمين
            similarity = SequenceMatcher(None, book_name.lower(), title.lower()).ratio()
            score = similarity * 10 + (ratings_count / 1000) + (rating / 10)

            if score > best_score:
                best_score = score
                best_match = href

        if best_match:
            return jsonify({"url": best_match})
        else:
            return jsonify({"url": None, "message": "لم يتم العثور على تطابق مناسب"})

    except Exception as e:
        print(f"Error fetching Goodreads link: {e}")
        return jsonify({"url": None, "message": "حدث خطأ"})

# ========== النسخ الاحتياطي ==========
@app.route("/backup")
def backup():
    if request.args.get("password") != ADMIN_PASSWORD:
        return "غير مصرح", 403
    return send_file(DATABASE, as_attachment=True, download_name="books_backup.db")

# ========== تصدير Excel ==========
@app.route("/export_excel")
def export_excel():
    if request.args.get("password") != ADMIN_PASSWORD:
        return "غير مصرح", 403

    mode = request.args.get("mode", "all")
    library_filter = request.args.get("library", "")

    conn = get_db()
    if mode == "library" and library_filter:
        rows = conn.execute(
            "SELECT * FROM books WHERE library = ? ORDER BY CAST(price AS REAL) DESC, id DESC",
            (library_filter,)
        ).fetchall()
        conn.close()
        df = pd.DataFrame([dict(row) for row in rows])
        cols = ["id", "book_name", "city", "library", "price", "publisher", "isbn", "cover_image"]
        df = df[cols] if all(col in df.columns for col in cols) else df

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=library_filter[:31])
        output.seek(0)
        filename = f"books_{library_filter}.xlsx"
        return send_file(output, as_attachment=True, download_name=filename,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # وضع all
    libraries = [row[0] for row in conn.execute("SELECT DISTINCT library FROM books WHERE library != '' ORDER BY library").fetchall()]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for lib in libraries:
            rows = conn.execute(
                "SELECT * FROM books WHERE library = ? ORDER BY CAST(price AS REAL) DESC, id DESC",
                (lib,)
            ).fetchall()
            if not rows:
                continue
            df = pd.DataFrame([dict(row) for row in rows])
            cols = ["id", "book_name", "city", "library", "price", "publisher", "isbn", "cover_image"]
            df = df[cols] if all(col in df.columns for col in cols) else df
            sheet_name = lib[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    conn.close()
    output.seek(0)
    filename = "books_all_libraries.xlsx"
    return send_file(output, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ========== لوحة التحكم ==========
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.args.get("password") != ADMIN_PASSWORD:
        return render_template_string("""
            <html dir="rtl"><body style="background:#0f172a;color:white;font-family:sans-serif;padding:20px">
            <h2>🔐 أدخل كلمة المرور</h2>
            <form method="get">
                <input type="password" name="password" placeholder="كلمة المرور" style="padding:10px;width:200px">
                <button type="submit" style="padding:10px 20px;background:#2563eb;color:white;border:none;border-radius:8px;cursor:pointer">دخول</button>
            </form>
            </body></html>
        """)

    conn = get_db()
    library_names = [row["library"] for row in conn.execute(
        "SELECT DISTINCT library FROM books WHERE library != '' ORDER BY library"
    ).fetchall()]
    selected_library = request.args.get("library", "")

    libraries = []
    for lib in library_names:
        safe_name = lib.replace(' ', '_')
        logo_url = None
        for ext in ['png', 'jpg', 'jpeg']:
            logo_path = f'logos/{safe_name}.{ext}'
            full_path = os.path.join(app.static_folder, logo_path)
            if os.path.exists(full_path):
                logo_url = urllib.parse.quote(logo_path)
                break
        libraries.append({'name': lib, 'logo': logo_url})

    if selected_library:
        all_books = conn.execute(
            "SELECT * FROM books WHERE library = ? ORDER BY id DESC",
            (selected_library,)
        ).fetchall()
    else:
        all_books = conn.execute(
            "SELECT * FROM books ORDER BY id DESC"
        ).fetchall()
    books_list = [dict(row) for row in all_books]
    conn.close()

    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "delete":
            book_id = request.form.get("id")
            conn = get_db()
            conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            conn.close()
            return jsonify({"status": "ok", "msg": "تم الحذف"})

        if action == "edit":
            book_id = request.form.get("id")
            conn = get_db()
            conn.execute("""UPDATE books SET 
                book_name=?, city=?, library=?, price=?, publisher=?, cover_image=?, isbn=?
                WHERE id=?""", (
                request.form["book_name"], request.form["city"], request.form["library"],
                request.form["price"], request.form["publisher"],
                request.form["cover_image"], request.form["isbn"],
                book_id))
            conn.commit()
            conn.close()
            return jsonify({"status": "ok", "msg": "تم التعديل"})

        if "file" in request.files and request.files["file"].filename != "":
            file = request.files["file"]
            filename = secure_filename(file.filename)
            filepath = os.path.join("/tmp", filename)
            file.save(filepath)
            target_library = request.form.get("target_library", "")
            new_library = request.form.get("new_library", "")
            final_library = new_library if new_library else target_library
            try:
                if filename.endswith(".csv"):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                df = df.fillna("")
                required_cols = ["book_name", "city", "library", "price", "publisher", "cover_image", "isbn"]
                for col in required_cols:
                    if col not in df.columns:
                        df[col] = ""
                if final_library:
                    df["library"] = final_library
                conn = get_db()
                count = 0
                for _, row in df.iterrows():
                    book_name = row.get("book_name", "")
                    if not book_name:
                        continue
                    exists = conn.execute(
                        "SELECT id FROM books WHERE book_name = ? AND library = ?",
                        (book_name, row.get("library", ""))
                    ).fetchone()
                    if not exists:
                        conn.execute("""INSERT INTO books (book_name, city, library, price, publisher, cover_image, isbn)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                            book_name, row.get("city", ""), row.get("library", ""),
                            str(row.get("price", "")), row.get("publisher", ""),
                            row.get("cover_image", ""), str(row.get("isbn", ""))))
                        count += 1
                conn.commit()
                conn.close()
                os.remove(filepath)
                msg = f"✅ تم استيراد {count} كتاباً جديداً!"
            except Exception as e:
                msg = f"❌ خطأ أثناء الاستيراد: {str(e)}"
            return render_template_string("<h2>{{ msg }}</h2><a href='/admin?password=" + ADMIN_PASSWORD + "&library=" + selected_library + "'>رجوع</a>", msg=msg)

        # إضافة كتاب واحد
        conn = get_db()
        conn.execute("""INSERT INTO books (book_name, city, library, price, publisher, cover_image, isbn)
            VALUES (?, ?, ?, ?, ?, ?, ?)""", (
            request.form["book_name"], request.form["city"], request.form["library"],
            request.form["price"], request.form["publisher"],
            request.form["cover_image"], request.form["isbn"]))
        conn.commit()
        conn.close()
        return redirect(f"/admin?password={ADMIN_PASSWORD}&library={selected_library}&msg=تمت الإضافة")

    # ---------- عرض الصفحة ----------
    return render_template_string("""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
      <meta charset="UTF-8">
      <title>لوحة التحكم – المكتبة الجامعة</title>
      <style>
        body { background:#0f172a; color:#e2e8f0; font-family:sans-serif; padding:20px; margin:0 }
        h2 { color:#fbbf24 }
        .top-bar { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px }
        .main-layout { display:flex; gap:20px; margin-top:20px; flex-wrap:wrap }
        .sidebar { background:#1e293b; border-radius:16px; padding:15px; min-width:200px; flex:0 0 220px }
        .sidebar h3 { color:#fbbf24; margin-bottom:10px }
        .sidebar a { display:flex; align-items:center; gap:8px; padding:8px 10px; color:#cbd5e1; text-decoration:none; border-radius:8px; margin:3px 0 }
        .sidebar a.active, .sidebar a:hover { background:#2563eb; color:white }
        .content { flex:1; min-width:0 }
        .panel { background:#1e293b; border-radius:16px; padding:20px; margin-bottom:20px }
        input,select,button { padding:10px; margin:5px 0; border-radius:8px; border:1px solid #334155; background:#0f172a; color:white; width:100%; box-sizing:border-box }
        button { background:#2563eb; cursor:pointer; border:none }
        button.danger { background:#dc2626 }
        button.success { background:#059669 }
        .filter-group { display:flex; gap:10px; flex-wrap:wrap }
        .filter-group input { flex:1; min-width:150px }
        table { width:100%; border-collapse:collapse; margin-top:10px; font-size:0.85em }
        th,td { border:1px solid #334155; padding:8px; text-align:right }
        th { background:#0f172a; color:#fbbf24 }
        .actions { display:flex; gap:5px }
        .actions button { width:auto; padding:4px 12px; font-size:0.8em }
        .counter { margin:10px 0 }
        .import-options { margin-top:10px; display:none }
      </style>
    </head>
    <body>
      <div class="top-bar">
        <h2>📚 لوحة تحكم المكتبة الجامعة</h2>
        <div style="display:flex; gap:10px; align-items:center;">
          <a href="/" target="_blank" style="color:#38bdf8">عرض الموقع</a>
          <a href="/backup?password={{ admin_password }}" style="color:#fbbf24; background:#1e293b; padding:6px 12px; border-radius:8px; text-decoration:none;">🗃️ نسخة احتياطية</a>
          <a href="/export_excel?password={{ admin_password }}&mode=all" style="color:#fbbf24; background:#1e293b; padding:6px 12px; border-radius:8px; text-decoration:none;">📥 تصدير Excel (الكل)</a>
          {% if selected_library %}
          <a href="/export_excel?password={{ admin_password }}&mode=library&library={{ selected_library }}" style="color:#fbbf24; background:#1e293b; padding:6px 12px; border-radius:8px; text-decoration:none;">📥 تصدير Excel ({{ selected_library }})</a>
          {% endif %}
        </div>
      </div>
      <div class="counter">عدد الكتب المعروضة: {{ books_count }}</div>

      <div class="main-layout">
        <div class="sidebar">
          <h3>🏛 المكتبات</h3>
          <a href="/admin?password={{ admin_password }}" class="{{ 'active' if not selected_library else '' }}">📋 الكل</a>
          {% for lib in libraries %}
          <a href="/admin?password={{ admin_password }}&library={{ lib.name }}" class="{{ 'active' if selected_library == lib.name else '' }}">
            {% if lib.logo %}
            <img src="/static/{{ lib.logo }}" style="width:28px; height:28px; border-radius:6px; object-fit:cover;" alt="">
            {% else %}
            <span style="width:28px; height:28px; border-radius:6px; background:#334155; display:inline-flex; align-items:center; justify-content:center;">🏛️</span>
            {% endif %}
            <span>{{ lib.name }}</span>
          </a>
          {% endfor %}
        </div>

        <div class="content">
          <!-- نماذج الإضافة والاستيراد -->
          <div style="display:flex; gap:20px; flex-wrap:wrap;">
            <div class="panel" style="flex:1; min-width:250px;">
              <h3>➕ إضافة كتاب واحد</h3>
              <form method="POST">
                <input name="book_name" placeholder="اسم الكتاب" required>
                <input name="city" placeholder="المدينة">
                <input name="library" placeholder="المكتبة">
                <input name="price" placeholder="السعر">
                <input name="publisher" placeholder="دار النشر">
                <input name="cover_image" placeholder="رابط صورة الغلاف">
                <input name="isbn" placeholder="ISBN">
                <button type="submit">إضافة</button>
              </form>
            </div>

            <div class="panel" style="flex:1; min-width:250px;">
              <h3>📁 استيراد جماعي ذكي</h3>
              <form method="POST" enctype="multipart/form-data">
                <label>اختر ملف (Excel أو CSV):</label>
                <input type="file" name="file" accept=".xlsx,.xls,.csv" required onchange="showImportOptions()">
                <div class="import-options" id="importOptions">
                  <label>اختر مكتبة موجودة:</label>
                  <select name="target_library">
                    <option value="">-- بدون تحديد (تستخدم الملف) --</option>
                    {% for lib in libraries %}
                    <option value="{{ lib.name }}">{{ lib.name }}</option>
                    {% endfor %}
                  </select>
                  <label>أو مكتبة جديدة:</label>
                  <input type="text" name="new_library" placeholder="اسم المكتبة الجديدة">
                </div>
                <button type="submit" class="success">استيراد الملف</button>
              </form>
              <p style="font-size:0.8em">الأعمدة المطلوبة: book_name, city, library, price, publisher, cover_image, isbn</p>
            </div>
          </div>

          <!-- الفلتر السريع -->
          <div class="panel">
            <h3>🔍 فلتر سريع</h3>
            <div class="filter-group">
              <input type="text" id="filterBookName" placeholder="اسم الكتاب" oninput="applyFilters()">
              <input type="text" id="filterLibrary" placeholder="المكتبة" oninput="applyFilters()">
              <input type="text" id="filterPublisher" placeholder="دار النشر" oninput="applyFilters()">
            </div>
          </div>

          <!-- جدول الكتب -->
          <div style="margin-top:20px; overflow-x:auto;">
            <table id="booksTable">
              <thead>
                <tr>
                  <th>ID</th><th>اسم الكتاب</th><th>المدينة</th><th>المكتبة</th><th>السعر</th><th>الناشر</th><th>ISBN</th><th>صورة</th><th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {% for b in books %}
                <tr id="row-{{ b.id }}">
                  <td>{{ b.id }}</td>
                  <td class="name">{{ b.book_name }}</td>
                  <td class="city">{{ b.city }}</td>
                  <td class="lib">{{ b.library }}</td>
                  <td class="price">{{ b.price }}</td>
                  <td class="pub">{{ b.publisher }}</td>
                  <td class="isbn">{{ b.isbn }}</td>
                  <td><img src="{{ b.cover_image or '/static/no-cover.png' }}" style="width:40px;height:auto;"></td>
                  <td class="actions">
                    <button onclick="editBook({{ b.id }})">✏️ تعديل</button>
                    <button class="danger" onclick="deleteBook({{ b.id }})">🗑️ حذف</button>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- نافذة التعديل -->
      <div id="editModal" style="display:none; position:fixed; top:10%; left:10%; right:10%; background:#1e293b; padding:20px; border-radius:20px; border:1px solid gold; z-index:1000">
        <h3>تعديل كتاب</h3>
        <form id="editForm">
          <input type="hidden" id="edit_id" name="id">
          <input id="edit_name" name="book_name" placeholder="اسم الكتاب" required>
          <input id="edit_city" name="city" placeholder="المدينة">
          <input id="edit_library" name="library" placeholder="المكتبة">
          <input id="edit_price" name="price" placeholder="السعر">
          <input id="edit_publisher" name="publisher" placeholder="دار النشر">
          <input id="edit_cover" name="cover_image" placeholder="رابط صورة الغلاف">
          <input id="edit_isbn" name="isbn" placeholder="ISBN">
          <button type="button" onclick="submitEdit()">حفظ التعديلات</button>
          <button type="button" class="danger" onclick="document.getElementById('editModal').style.display='none'">إلغاء</button>
        </form>
      </div>

      <script>
        const ADMIN_PASSWORD = "{{ admin_password }}";
        function showImportOptions() {
            document.getElementById("importOptions").style.display = "block";
        }
        function applyFilters() {
            let nameFilter = document.getElementById("filterBookName").value.toLowerCase().trim();
            let libFilter = document.getElementById("filterLibrary").value.toLowerCase().trim();
            let pubFilter = document.getElementById("filterPublisher").value.toLowerCase().trim();
            let table = document.getElementById("booksTable");
            let tr = table.getElementsByTagName("tr");
            for (let i = 1; i < tr.length; i++) {
                let cells = tr[i].getElementsByTagName("td");
                if (cells.length < 8) continue;
                let name = (cells[1]?.textContent || "").toLowerCase();
                let lib = (cells[3]?.textContent || "").toLowerCase();
                let pub = (cells[5]?.textContent || "").toLowerCase();
                let match = true;
                if (nameFilter && !name.includes(nameFilter)) match = false;
                if (libFilter && !lib.includes(libFilter)) match = false;
                if (pubFilter && !pub.includes(pubFilter)) match = false;
                tr[i].style.display = match ? "" : "none";
            }
        }
        function editBook(id) {
            let row = document.getElementById("row-" + id);
            document.getElementById("edit_id").value = id;
            document.getElementById("edit_name").value = row.querySelector(".name").textContent.trim();
            document.getElementById("edit_city").value = row.querySelector(".city").textContent.trim();
            document.getElementById("edit_library").value = row.querySelector(".lib").textContent.trim();
            document.getElementById("edit_price").value = row.querySelector(".price").textContent.trim();
            document.getElementById("edit_publisher").value = row.querySelector(".pub").textContent.trim();
            document.getElementById("edit_isbn").value = row.querySelector(".isbn").textContent.trim();
            document.getElementById("edit_cover").value = row.querySelector("img")?.src || "";
            document.getElementById("editModal").style.display = "block";
        }
        function submitEdit() {
            let form = document.getElementById("editForm");
            let formData = new FormData(form);
            formData.append("action", "edit");
            fetch("/admin?password=" + ADMIN_PASSWORD, {
                method: "POST",
                body: formData
            }).then(response => response.json()).then(data => {
                alert(data.msg);
                location.reload();
            }).catch(err => alert("خطأ"));
        }
        function deleteBook(id) {
            if (confirm("هل أنت متأكد من حذف هذا الكتاب؟")) {
                let formData = new FormData();
                formData.append("id", id);
                formData.append("action", "delete");
                fetch("/admin?password=" + ADMIN_PASSWORD, {
                    method: "POST",
                    body: formData
                }).then(response => response.json()).then(data => {
                    alert(data.msg);
                    document.getElementById("row-" + id).remove();
                }).catch(err => alert("خطأ"));
            }
        }
      </script>
    </body>
    </html>
    """, books=books_list, books_count=len(books_list), admin_password=ADMIN_PASSWORD, libraries=libraries, selected_library=selected_library)

@app.route("/")
def home():
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route("/search")
def api():
    q = request.args.get("q", "")
    return jsonify(search(q))

@app.route("/filters_data")
def filters_data():
    conn = get_db()
    cities = [row[0] for row in conn.execute("SELECT DISTINCT city FROM books WHERE city != '' ORDER BY city").fetchall()]
    libraries = [row[0] for row in conn.execute("SELECT DISTINCT library FROM books WHERE library != '' ORDER BY library").fetchall()]
    publishers = [row[0] for row in conn.execute("SELECT DISTINCT publisher FROM books WHERE publisher != '' ORDER BY publisher").fetchall()]
    min_price = conn.execute("SELECT MIN(CAST(price AS REAL)) FROM books WHERE price != '' AND price IS NOT NULL").fetchone()[0] or 0
    max_price = conn.execute("SELECT MAX(CAST(price AS REAL)) FROM books WHERE price != '' AND price IS NOT NULL").fetchone()[0] or 0
    conn.close()
    return jsonify({
        "cities": cities,
        "libraries": libraries,
        "publishers": publishers,
        "min_price": min_price,
        "max_price": max_price
    })

@app.route("/initial_books")
def initial_books():
    conn = get_db()
    books = conn.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 24").fetchall()
    conn.close()
    return jsonify([dict(row) for row in books])

if __name__ == "__main__":
    app.run(port=5000, debug=True)
