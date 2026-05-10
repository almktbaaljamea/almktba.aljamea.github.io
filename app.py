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

app = Flask(__name__)

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
                  <td><img src="{{ b.cover_image or 'https://via.placeholder.com/40' }}" style="width:40px;height:auto;"></td>
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

# ========== واجهة المستخدم (المكتبة الجامعة) – تم تحديثها بميزة الـ Loader وإصلاح تضارب الكتب ==========
HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>المكتبة الجامعة – محرك بحث الكتب</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #0f172a; color: #e2e8f0; }
    .container { max-width: 950px; margin: auto; padding: 20px; }

    .header-section {
      text-align: center; margin-bottom: 35px; padding-bottom: 20px;
      border-bottom: 1px solid #334155;
    }
    .logo-img {
      width: 130px; height: 130px; max-width: 100%;
      border-radius: 50%; object-fit: cover; margin-bottom: 15px;
      box-shadow: 0 0 15px rgba(251,191,36,0.3);
    }
    .main-title {
      font-size: 2.3em; margin: 10px 0 5px;
      background: linear-gradient(to left, #fbbf24, #f59e0b);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      font-weight: bold;
    }
    .slogan { color: #fbbf24; font-size: 1.1em; margin: 8px 0 5px; font-style: italic; }
    .sub-slogan { color: #94a3b8; font-size: 0.9em; margin-top: 6px; }

    .search-box { margin-bottom: 20px; display: flex; gap: 10px; }
    input {
      flex: 1; padding: 14px 18px; border-radius: 14px;
      border: 1px solid #334155; background: #1e293b; color: white; font-size: 16px;
    }
    input:focus { outline: none; border-color: #38bdf8; }

    .filter-toggle-btn {
      padding: 14px 20px; border-radius: 14px; border: 1px solid #334155;
      background: #1e293b; color: #fbbf24; font-size: 16px; cursor: pointer;
      transition: 0.2s; white-space: nowrap;
    }
    .filter-toggle-btn:hover { background: #2563eb; color: white; border-color: #2563eb; }

    #resultCount { font-size: 0.9em; color: #94a3b8; margin-bottom: 15px; }

    .city-card {
      background: linear-gradient(145deg, #1e293b, #0f172a);
      margin-top: 18px; padding: 18px; border-radius: 18px;
      border: 1px solid #334155; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .city-name { font-size: 1.4em; color: #38bdf8; margin-bottom: 12px; }
    .library-name { color: #fbbf24; font-weight: bold; margin: 15px 0 10px; font-size: 1.2em; }

    .books-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px; margin-right: 15px;
    }
    .book-card {
      background: #1e293b; border-radius: 14px; overflow: hidden;
      display: flex; border: 1px solid #334155; cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .book-card:hover { transform: translateY(-3px); box-shadow: 0 8px 18px rgba(0,0,0,0.5); }
    .book-card img { width: 80px; height: 110px; object-fit: cover; border-left: 1px solid #334155; }
    .book-details { padding: 12px; display: flex; flex-direction: column; justify-content: center; }
    .book-title { font-weight: bold; font-size: 1em; margin-bottom: 4px; color: #f1f5f9; }
    .book-publisher { font-size: 0.85em; color: #94a3b8; margin-bottom: 4px; }
    .book-price { color: #4ade80; font-weight: bold; font-size: 1.1em; }

    .no-results { text-align: center; margin-top: 50px; color: #94a3b8; font-size: 1.2em; }

    /* نافذة الفلاتر */
    .filter-modal {
      display: none; position: fixed; z-index: 1000; left: 0; top: 0;
      width: 100%; height: 100%; overflow: auto;
      background-color: rgba(0,0,0,0.75); backdrop-filter: blur(4px);
    }
    .filter-modal-content {
      background: #1e293b; margin: 3% auto; padding: 25px;
      border-radius: 20px; border: 1px solid #334155;
      width: 90%; max-width: 650px;
    }
    .filter-section { margin-bottom: 20px; }
    .filter-section h4 { color: #fbbf24; margin-bottom: 8px; }
    .filter-search {
      width: 100%; padding: 8px 12px; margin-bottom: 8px;
      border-radius: 8px; border: 1px solid #334155;
      background: #0f172a; color: white; font-size: 0.9em;
    }
    .checkbox-group {
      max-height: 150px; overflow-y: auto;
      border: 1px solid #334155; border-radius: 8px;
      padding: 8px; background: #0f172a;
      display: flex; flex-wrap: wrap; gap: 6px; align-content: flex-start;
    }
    .checkbox-group label {
      display: flex; align-items: center; gap: 4px;
      background: #1e293b; padding: 4px 10px; border-radius: 6px;
      font-size: 0.85em; cursor: pointer; white-space: nowrap;
    }
    .select-all { color: #38bdf8; font-weight: bold; }
    .price-range { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .price-range input { width: 100px; padding: 8px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; }
    .filter-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
    .filter-actions button { padding: 12px 24px; border-radius: 10px; border: none; cursor: pointer; font-size: 1em; }
    .apply-btn { background: #2563eb; color: white; }
    .apply-btn:hover { background: #1d4ed8; }
    .reset-btn { background: #334155; color: white; }
    .reset-btn:hover { background: #475569; }

    /* نافذة تفاصيل الكتاب */
    .modal {
      display: none; position: fixed; z-index: 2000; left: 0; top: 0;
      width: 100%; height: 100%; overflow: auto;
      background-color: rgba(0,0,0,0.75); backdrop-filter: blur(4px);
    }
    .modal-content {
      background: #1e293b; margin: 5% auto; padding: 25px;
      border-radius: 20px; border: 1px solid #334155;
      width: 90%; max-width: 650px; position: relative;
    }
    .close {
      position: absolute; top: 10px; left: 20px; color: #94a3b8;
      font-size: 30px; font-weight: bold; cursor: pointer;
    }
    .close:hover { color: #fbbf24; }
    .modal-book-header { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
    .modal-book-header img { width: 150px; height: 220px; object-fit: cover; border-radius: 12px; border: 1px solid #334155; }
    .modal-book-info { flex: 1; min-width: 250px; }
    .modal-book-info h2 { color: #fbbf24; margin-bottom: 8px; font-size: 1.5em; }
    .modal-book-info p { margin: 6px 0; color: #cbd5e1; font-size: 1em; }
    .modal-book-info .price { color: #4ade80; font-weight: bold; font-size: 1.3em; }
    .rating-section {
      margin-top: 15px; padding: 12px; background: #0f172a;
      border-radius: 12px; display: flex; flex-direction: column; gap: 12px;
    }
    .goodreads-btn, .googlebooks-btn {
      display: block; padding: 12px 20px;
      background: #382110; color: #f3d9b1; border-radius: 10px;
      text-decoration: none; font-size: 1em; text-align: center; transition: 0.2s;
      cursor: pointer;
    }
    .goodreads-btn:hover { background: #4a2c1a; }
    .googlebooks-btn { background: #2563eb; color: white; }
    .googlebooks-btn:hover { background: #1d4ed8; }
    .share-btn {
      display: inline-block; margin-top: 10px; padding: 10px 20px;
      background: #334155; color: white; border-radius: 10px;
      cursor: pointer; border: none; font-size: 1em;
    }
    .share-btn:hover { background: #475569; }

    /* شاشة التحميل العامة */
    .global-loader {
      display: none; position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(6px);
      z-index: 9999; flex-direction: column; justify-content: center; align-items: center;
    }
    .global-loader img {
      width: 110px; height: 110px;
      border-radius: 50%;
      box-shadow: 0 0 20px rgba(251,191,36,0.6);
      animation: pulse 1.5s infinite;
    }
    .global-loader p {
      color: #fbbf24; margin-top: 20px; font-size: 1.3em; font-weight: bold;
    }
    @keyframes pulse {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.7); }
      70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(251, 191, 36, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(251, 191, 36, 0); }
    }

    @media (max-width: 600px) {
      .search-box { flex-direction: column; }
      .filter-toggle-btn { width: 100%; }
      .modal-book-header { flex-direction: column; align-items: center; text-align: center; }
      .modal-book-header img { width: 180px; height: 260px; }
    }
  </style>
</head>
<body>
  <!-- شاشة التحميل العامة -->
  <div id="globalLoader" class="global-loader">
    <img src="/static/logo.png" alt="جاري التحميل">
    <p id="loaderText">جاري التحميل...</p>
  </div>

  <div class="container">
    <div class="header-section">
      <img src="/static/logo.png" alt="شعار المكتبة الجامعة" class="logo-img">
      <h1 class="main-title">المكتبة الجامعة</h1>
      <p class="slogan">تَجْمَعُ الْمَعْرِفَةَ لِتَصِلْ إِلَيْكَ</p>
      <p class="sub-slogan">وجهتك الأولى للعثور على أي كتاب من أي مكتبة</p>
    </div>

    <div class="search-box">
      <input type="text" id="searchInput" placeholder="اكتب اسم الكتاب..." autocomplete="off">
      <button class="filter-toggle-btn" onclick="openFilterModal()">⚙️ الفلتر</button>
    </div>

    <div id="resultCount"></div>
    <div id="results"></div>
  </div>

  <!-- نافذة الفلاتر -->
  <div id="filterModal" class="filter-modal">
    <div class="filter-modal-content">
      <h3 style="color:#fbbf24; margin-bottom:20px;">تخصيص البحث</h3>
      <div class="filter-section">
        <h4>🏙️ المدن</h4>
        <input type="text" class="filter-search" placeholder="بحث عن مدينة..." oninput="filterGroup('citiesGroup', this.value)">
        <div class="checkbox-group" id="citiesGroup"></div>
      </div>
      <div class="filter-section">
        <h4>🏛️ المكتبات</h4>
        <input type="text" class="filter-search" placeholder="بحث عن مكتبة..." oninput="filterGroup('librariesGroup', this.value)">
        <div class="checkbox-group" id="librariesGroup"></div>
      </div>
      <div class="filter-section">
        <h4>📘 دور النشر</h4>
        <input type="text" class="filter-search" placeholder="بحث عن دار نشر..." oninput="filterGroup('publishersGroup', this.value)">
        <div class="checkbox-group" id="publishersGroup"></div>
      </div>
      <div class="filter-section">
        <h4>💰 السعر</h4>
        <div class="price-range">
          <input type="number" id="priceFrom" placeholder="من" min="0" step="any">
          <span>–</span>
          <input type="number" id="priceTo" placeholder="إلى" min="0" step="any">
        </div>
      </div>
      <div class="filter-actions">
        <button class="reset-btn" onclick="resetFilters()">إعادة تعيين</button>
        <button class="apply-btn" onclick="applyFilters()">تطبيق الفلاتر</button>
      </div>
    </div>
  </div>

  <!-- نافذة تفاصيل الكتاب -->
  <div id="bookModal" class="modal">
    <div class="modal-content">
      <span class="close" onclick="closeModal()">&times;</span>
      <div id="modalBody"></div>
    </div>
  </div>

  <script>
    if (window.Telegram && Telegram.WebApp) {
      Telegram.WebApp.ready();
      Telegram.WebApp.setHeaderColor('#0f172a');
      Telegram.WebApp.setBackgroundColor('#0f172a');
    }

    let currentResults = [];

    // دوال التحكم في شاشة التحميل
    function showLoader(text = "جاري التحميل...") {
      document.getElementById('loaderText').innerHTML = text;
      document.getElementById('globalLoader').style.display = 'flex';
    }
    function hideLoader() {
      document.getElementById('globalLoader').style.display = 'none';
    }

    // ---------- دوال الفلاتر ----------
    function getUniqueValues(data, key) {
      return [...new Set(data.map(b => b[key]).filter(v => v))];
    }

    function buildCheckboxGroup(containerId, items, prefix, defaultAllChecked = true) {
      const container = document.getElementById(containerId);
      container.innerHTML = '';
      const allLabel = document.createElement('label');
      allLabel.className = 'select-all';
      allLabel.innerHTML = `<input type="checkbox" id="${prefix}_all" ${defaultAllChecked ? 'checked' : ''} onchange="toggleSelectAll('${prefix}', this.checked)"> الكل`;
      container.appendChild(allLabel);
      items.forEach(item => {
        const label = document.createElement('label');
        label.innerHTML = `<input type="checkbox" class="${prefix}-item" value="${item}" ${defaultAllChecked ? 'checked' : ''} onchange="onItemChange('${prefix}')"> ${item}`;
        container.appendChild(label);
      });
    }

    function onItemChange(prefix) {
      const allItems = document.querySelectorAll(`.${prefix}-item`);
      const allChecked = Array.from(allItems).every(cb => cb.checked);
      document.getElementById(`${prefix}_all`).checked = allChecked;
      if (prefix === 'city') updateLibrariesBasedOnSelectedCities(false);
      else if (prefix === 'library') updatePublishersBasedOnSelectedLibraries();
    }

    function toggleSelectAll(prefix, isChecked) {
      document.querySelectorAll(`.${prefix}-item`).forEach(cb => cb.checked = isChecked);
      if (prefix === 'city') updateLibrariesBasedOnSelectedCities(true);
      else if (prefix === 'library') updatePublishersBasedOnSelectedLibraries();
    }

    function getSelectedValues(prefix) {
      return Array.from(document.querySelectorAll(`.${prefix}-item:checked`)).map(cb => cb.value);
    }

    function updateLibrariesBasedOnSelectedCities(keepLibraryAll = false) {
      const selectedCities = getSelectedValues('city');
      const allCitiesChecked = document.getElementById('city_all').checked;
      let filtered = currentResults;
      if (!allCitiesChecked && selectedCities.length > 0) filtered = filtered.filter(b => selectedCities.includes(b.city));
      const libraries = getUniqueValues(filtered, 'library');
      buildCheckboxGroup('librariesGroup', libraries, 'library', keepLibraryAll);
      if (!keepLibraryAll) {
        const libraryAll = document.getElementById('library_all');
        if (libraryAll) libraryAll.checked = false;
        document.querySelectorAll('.library-item').forEach(cb => cb.checked = false);
      }
      updatePublishersBasedOnSelectedLibraries();
    }

    function updatePublishersBasedOnSelectedLibraries() {
      const selectedCities = getSelectedValues('city');
      const selectedLibraries = getSelectedValues('library');
      const allCitiesChecked = document.getElementById('city_all')?.checked ?? true;
      const allLibrariesChecked = document.getElementById('library_all')?.checked ?? false;
      let filtered = currentResults;
      if (!allCitiesChecked && selectedCities.length > 0) filtered = filtered.filter(b => selectedCities.includes(b.city));
      if (!allLibrariesChecked) {
        if (selectedLibraries.length > 0) filtered = filtered.filter(b => selectedLibraries.includes(b.library));
        else { buildCheckboxGroup('publishersGroup', [], 'publisher', false); return; }
      }
      const publishers = getUniqueValues(filtered, 'publisher');
      buildCheckboxGroup('publishersGroup', publishers, 'publisher', allLibrariesChecked);
    }

    function rebuildAllGroups(defaultAll = true) {
      if (currentResults.length === 0) {
        buildCheckboxGroup('citiesGroup', [], 'city', false);
        buildCheckboxGroup('librariesGroup', [], 'library', false);
        buildCheckboxGroup('publishersGroup', [], 'publisher', false);
        return;
      }
      buildCheckboxGroup('citiesGroup', getUniqueValues(currentResults, 'city'), 'city', defaultAll);
      buildCheckboxGroup('librariesGroup', getUniqueValues(currentResults, 'library'), 'library', defaultAll);
      buildCheckboxGroup('publishersGroup', getUniqueValues(currentResults, 'publisher'), 'publisher', defaultAll);
    }

    function filterGroup(groupId, searchText) {
      const container = document.getElementById(groupId);
      const labels = container.getElementsByTagName('label');
      for (let i = 1; i < labels.length; i++) labels[i].style.display = labels[i].textContent.toLowerCase().includes(searchText.toLowerCase()) ? '' : 'none';
    }

    function openFilterModal() {
      if (currentResults.length > 0) rebuildAllGroups(true);
      document.getElementById('filterModal').style.display = 'block';
    }

    function applyFilters() {
      document.getElementById('filterModal').style.display = 'none';
      applyFiltersAndRender();
    }

    function resetFilters() {
      rebuildAllGroups(true);
      document.getElementById('priceFrom').value = '';
      document.getElementById('priceTo').value = '';
      applyFiltersAndRender();
      document.getElementById('filterModal').style.display = 'none';
    }

    window.addEventListener('click', function(event) {
      if (event.target == document.getElementById('filterModal')) document.getElementById('filterModal').style.display = 'none';
      if (event.target == document.getElementById('bookModal')) closeModal();
    });

    // ---------- تحميل الكتب الأولية (مع Loader) ----------
    window.addEventListener('DOMContentLoaded', () => {
      showLoader("جاري تحميل الكتب المقترحة...");
      fetch('/initial_books')
        .then(res => res.json())
        .then(data => {
          currentResults = data;
          applyFiltersAndRender();
          hideLoader();
        })
        .catch(err => {
          console.error(err);
          hideLoader();
        });
    });

    // ---------- البحث المباشر (مع Loader) ----------
    let debounceTimer;
    document.getElementById('searchInput').addEventListener('input', function() {
      clearTimeout(debounceTimer);
      const query = this.value.trim();
      if (query.length < 2) {
        showLoader("جاري تحميل الكتب المقترحة...");
        fetch('/initial_books')
          .then(res => res.json())
          .then(data => {
            currentResults = data;
            applyFiltersAndRender();
            hideLoader();
          });
        return;
      }
      showLoader("جاري البحث عن الكتب...");
      debounceTimer = setTimeout(() => {
        fetch(`/search?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
            currentResults = data;
            applyFiltersAndRender();
            hideLoader();
          })
          .catch(err => {
            console.error(err);
            document.getElementById('results').innerHTML = '<div class="no-results">⚠️ خطأ في الاتصال</div>';
            hideLoader();
          });
      }, 300);
    });

    function applyFiltersAndRender() {
      let filtered = [...currentResults];
      const cityCheckboxes = document.querySelectorAll('.city-item:checked');
      const libraryCheckboxes = document.querySelectorAll('.library-item:checked');
      const publisherCheckboxes = document.querySelectorAll('.publisher-item:checked');
      const cityAll = document.getElementById('city_all');
      const libraryAll = document.getElementById('library_all');
      const publisherAll = document.getElementById('publisher_all');
      const filterCities = (cityAll && !cityAll.checked) ? Array.from(cityCheckboxes).map(cb => cb.value) : null;
      const filterLibraries = (libraryAll && !libraryAll.checked) ? Array.from(libraryCheckboxes).map(cb => cb.value) : null;
      const filterPublishers = (publisherAll && !publisherAll.checked) ? Array.from(publisherCheckboxes).map(cb => cb.value) : null;
      if (filterCities) filtered = filtered.filter(b => filterCities.includes(b.city));
      if (filterLibraries) filtered = filtered.filter(b => filterLibraries.includes(b.library));
      if (filterPublishers) filtered = filtered.filter(b => filterPublishers.includes(b.publisher));
      const from = parseFloat(document.getElementById('priceFrom').value);
      const to = parseFloat(document.getElementById('priceTo').value);
      if (!isNaN(from) || !isNaN(to)) {
        filtered = filtered.filter(b => {
          const p = parseFloat(b.price);
          if (isNaN(p)) return false;
          if (!isNaN(from) && p < from) return false;
          if (!isNaN(to) && p > to) return false;
          return true;
        });
      }
      const searchQuery = document.getElementById('searchInput').value.trim();
      const countText = searchQuery.length >= 2 ? `تم العثور على <strong>${filtered.length}</strong> كتاب` : `<strong>${filtered.length}</strong> كتاب مقترح`;
      document.getElementById('resultCount').innerHTML = countText;
      if (filtered.length === 0) {
        document.getElementById('results').innerHTML = '<div class="no-results">🔍 لا توجد نتائج مطابقة</div>';
        return;
      }
      const grouped = {};
      filtered.forEach(b => {
        const c = b.city || 'غير معروف', lib = b.library || 'مكتبة غير محددة';
        if (!grouped[c]) grouped[c] = {};
        if (!grouped[c][lib]) grouped[c][lib] = [];
        grouped[c][lib].push(b);
      });
      let html = '';
      for (const city in grouped) {
        html += `<div class="city-card"><div class="city-name">📍 ${city}</div>`;
        for (const lib in grouped[city]) {
          html += `<div class="library-name">🏛 ${lib}</div><div class="books-grid">`;
          grouped[city][lib].forEach(book => {
            const img = book.cover_image || 'https://via.placeholder.com/80x110/1e293b/94a3b8?text=No+Cover';
            // ✅ التعديل الأول: استخدام book.id بدلاً من book.book_name
            html += `
              <div class="book-card" onclick="openBookModal(${book.id})">
                <img src="${img}" alt="${book.book_name}" loading="lazy">
                <div class="book-details">
                  <div class="book-title">${book.book_name || '---'}</div>
                  <div class="book-publisher">📘 ${book.publisher || 'غير معروف'}</div>
                  <div class="book-price">💰 ${book.price || '0'}</div>
                </div>
              </div>`;
          });
          html += `</div>`;
        }
        html += `</div>`;
      }
      document.getElementById('results').innerHTML = html;
    }

    // ✅ التعديل الثاني: تحديث دالة openBookModal لتعمل بالمعرف bookId
    function openBookModal(bookId) {
      const book = currentResults.find(b => b.id == bookId);
      if (!book) return;
      const body = document.getElementById('modalBody');
      const imgSrc = book.cover_image || 'https://via.placeholder.com/150x220/1e293b/94a3b8?text=No+Cover';
      const googleBooksSearchUrl = `https://www.google.com/search?tbm=bks&q=${encodeURIComponent(book.book_name)}`;
      body.innerHTML = `
        <div class="modal-book-header">
          <img src="${imgSrc}" alt="${book.book_name}">
          <div class="modal-book-info">
            <h2>${book.book_name}</h2>
            <p>📘 الناشر: ${book.publisher || 'غير معروف'}</p>
            <p>🏛 المكتبة: ${book.library || 'غير محددة'}</p>
            <p>📍 المدينة: ${book.city || 'غير محددة'}</p>
            <p class="price">💰 السعر: ${book.price || 'غير متوفر'}</p>
            <div class="rating-section">
              <div class="goodreads-btn" onclick="openGoodreads('${encodeURIComponent(book.book_name)}')">📊 تقييمات ومراجعات Goodreads</div>
              <a href="${googleBooksSearchUrl}" target="_blank" class="googlebooks-btn">📖 آراء Google Books</a>
            </div>
            <button class="share-btn" onclick="shareBook('${book.book_name}')">📤 مشاركة الكتاب</button>
          </div>
        </div>
      `;
      document.getElementById('bookModal').style.display = 'block';
    }

    // دالة Goodreads مع الـ Loader
    function openGoodreads(encodedBookName) {
      const bookName = decodeURIComponent(encodedBookName);
      showLoader("جاري البحث عن التقييمات...");
      fetch(`/get_goodreads_link?q=${encodeURIComponent(bookName)}`)
        .then(response => response.json())
        .then(data => {
          hideLoader();
          if (data.url) {
            window.open(data.url, '_blank');
          } else {
            window.open(`https://www.goodreads.com/search?q=${encodeURIComponent(bookName)}`, '_blank');
          }
        })
        .catch(() => {
          hideLoader();
          window.open(`https://www.goodreads.com/search?q=${encodeURIComponent(bookName)}`, '_blank');
        });
    }

    function shareBook(bookName) {
      const text = `📚 أنصحك بقراءة هذا الكتاب: "${bookName}"`;
      if (navigator.share) navigator.share({ title: 'مشاركة كتاب', text: text }).catch(()=>{});
      else {
        navigator.clipboard.writeText(text).then(() => alert('تم نسخ اسم الكتاب!')).catch(() => prompt('انسخ اسم الكتاب:', text));
      }
    }

    function closeModal() { document.getElementById('bookModal').style.display = 'none'; }
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

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
