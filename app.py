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

app = Flask(__name__, static_folder='out')
# مسار قاعدة البيانات
DATABASE = os.path.join(os.path.dirname(__file__), "books.db")

# كلمة مرور لوحة التحكم (غيّرها كما تريد)
ADMIN_PASSWORD = "hasanbook2007"

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

    # إنشاء جدول إعدادات المكتبات (أرقام واتساب)
    try:
        conn = sqlite3.connect(DATABASE)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS library_settings (
                library_name TEXT PRIMARY KEY,
                whatsapp_number TEXT DEFAULT '',
                location_link TEXT DEFAULT '',
                description TEXT DEFAULT ''
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("❌ خطأ أثناء إنشاء جدول إعدادات المكتبات:", e)

# تشغيل التهيئة
init_db()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ========== البحث في قاعدة البيانات ==========
def search(query, library=""):
    conn = get_db()
    sql = """SELECT b.*, COALESCE(ls.whatsapp_number, '') as whatsapp_number
             FROM books b LEFT JOIN library_settings ls ON b.library = ls.library_name
             WHERE 1=1"""
    params = []
    if query:
        sql += " AND b.book_name LIKE ?"
        params.append(f'%{query}%')
    if library:
        sql += " AND b.library = ?"
        params.append(library)
        
    results = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in results]

# ========== نقطة النهاية الذكية لـ Goodreads ==========
@app.route("/get_goodreads_link")
def get_goodreads_link():
    book_name = request.args.get("q", "").strip()
    if not book_name:
        return jsonify({"error": "No query"}), 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    }

    # المحاولة الأولى: رابط البحث المباشر بالعنوان (غالباً يحول لصفحة الكتاب فوراً)
    title_url = f"https://www.goodreads.com/book/title?title={requests.utils.quote(book_name)}"
    
    try:
        session = requests.Session()
        # محاولة الوصول المباشر
        resp = session.get(title_url, headers=headers, timeout=10, allow_redirects=True)
        
        # إذا تحول الرابط لصفحة كتاب محددة
        if "/book/show/" in resp.url:
            return jsonify({"url": resp.url})

        # المحاولة الثانية: البحث والفلترة (إذا لم ينجح التحويل المباشر)
        search_url = f"https://www.goodreads.com/search?q={requests.utils.quote(book_name)}"
        resp = session.get(search_url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            # إذا فشل الاتصال، نعيد رابط التحويل المباشر لفتحه من المتصفح (client-side)
            return jsonify({"url": title_url})

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="tableList")
        if not table:
            return jsonify({"url": title_url})

        rows = table.find_all("tr")
        best_match = None
        best_score = -1

        for row in rows:
            link_tag = row.find("a", class_="bookTitle")
            if not link_tag: continue

            title = link_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            if not href.startswith("http"):
                href = "https://www.goodreads.com" + href

            # استخراج التقييمات
            rating = 0.0
            ratings_count = 0
            rating_span = row.find("span", class_="minirating")
            if rating_span:
                text = rating_span.get_text()
                r_match = re.search(r'(\d+\.?\d*)\s*avg', text)
                c_match = re.search(r'(\d[\d,]*)\s*ratings', text)
                if r_match: rating = float(r_match.group(1))
                if c_match: ratings_count = int(c_match.group(1).replace(',', ''))

            similarity = SequenceMatcher(None, book_name.lower(), title.lower()).ratio()
            score = similarity * 10 + (ratings_count / 1000) + (rating / 10)

            if score > best_score:
                best_score = score
                best_match = href

        return jsonify({"url": best_match if best_match else title_url})

    except Exception as e:
        print(f"Goodreads Redirect Error: {e}")
        return jsonify({"url": title_url})




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
    city_filter = request.args.get("city", "")

    conn = get_db()
    if mode == "library" and (library_filter or city_filter):
        query = "SELECT * FROM books WHERE 1=1"
        params = []
        if library_filter:
            query += " AND library = ?"
            params.append(library_filter)
        if city_filter:
            query += " AND city = ?"
            params.append(city_filter)
            
        query += " ORDER BY CAST(price AS REAL) DESC, id DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        df = pd.DataFrame([dict(row) for row in rows])
        cols = ["id", "book_name", "city", "library", "price", "publisher", "isbn", "cover_image"]
        df = df[cols] if all(col in df.columns for col in cols) else df

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            sheet_name = (library_filter or city_filter)[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)
        filename = f"books_export.xlsx"
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
            <html dir="rtl"><body style="background:#0f172a;color:white;font-family:sans-serif;padding:20px;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
            <div style="background:rgba(30, 41, 59, 0.7);backdrop-filter:blur(10px);padding:40px;border-radius:20px;border:1px solid rgba(255,255,255,0.1);text-align:center;box-shadow:0 10px 30px rgba(0,0,0,0.5);">
                <h2 style="color:#fbbf24;margin-bottom:20px;">🔐 لوحة تحكم المكتبة الجامعة</h2>
                <form method="get">
                    <input type="password" name="password" placeholder="أدخل كلمة المرور" style="padding:12px;width:250px;border-radius:10px;border:1px solid #334155;background:#0f172a;color:white;outline:none;">
                    <br><br>
                    <button type="submit" style="padding:12px 30px;background:#2563eb;color:white;border:none;border-radius:10px;cursor:pointer;font-weight:bold;transition:0.3s;" onmouseover="this.style.background='#1d4ed8'" onmouseout="this.style.background='#2563eb'">دخول</button>
                </form>
            </div>
            </body></html>
        """)

    conn = get_db()
    
    # إحصائيات سريعة
    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    total_libraries = conn.execute("SELECT COUNT(DISTINCT library) FROM books WHERE library != ''").fetchone()[0]
    total_cities = conn.execute("SELECT COUNT(DISTINCT city) FROM books WHERE city != ''").fetchone()[0]
    total_publishers = conn.execute("SELECT COUNT(DISTINCT publisher) FROM books WHERE publisher != ''").fetchone()[0]
    
    # جلب قوائم الفلترة
    library_names = [row["library"] for row in conn.execute("SELECT DISTINCT library FROM books WHERE library != '' ORDER BY library").fetchall()]
    city_names = [row["city"] for row in conn.execute("SELECT DISTINCT city FROM books WHERE city != '' ORDER BY city").fetchall()]
    
    selected_library = request.args.get("library", "")
    selected_city = request.args.get("city", "")
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    per_page = 50

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

    if request.method == "POST":
        action = request.form.get("action", "")
        
        if action == "delete":
            book_id = request.form.get("id")
            conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            return jsonify({"status": "ok", "msg": "تم الحذف بنجاح"})
            
        if action == "bulk_delete":
            ids = request.form.getlist("ids[]")
            if ids:
                placeholders = ','.join('?' * len(ids))
                conn.execute(f"DELETE FROM books WHERE id IN ({placeholders})", ids)
                conn.commit()
            return jsonify({"status": "ok", "msg": f"تم حذف {len(ids)} كتاب بنجاح"})

        if action == "edit":
            book_id = request.form.get("id")
            conn.execute("""UPDATE books SET 
                book_name=?, city=?, library=?, price=?, publisher=?, cover_image=?, isbn=?
                WHERE id=?""", (
                request.form["book_name"], request.form["city"], request.form["library"],
                request.form["price"], request.form["publisher"],
                request.form["cover_image"], request.form["isbn"],
                book_id))
            conn.commit()
            return jsonify({"status": "ok", "msg": "تم التعديل"})

        if action == "add":
            conn.execute("""INSERT INTO books (book_name, city, library, price, publisher, cover_image, isbn)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                request.form["book_name"], request.form["city"], request.form["library"],
                request.form["price"], request.form["publisher"],
                request.form["cover_image"], request.form["isbn"]))
            conn.commit()
            return redirect(f"/admin?password={ADMIN_PASSWORD}&library={selected_library}&city={selected_city}&msg={urllib.parse.quote('تمت الإضافة بنجاح')}")

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
                os.remove(filepath)
                msg = f"✅ تم استيراد {count} كتاباً جديداً!"
            except Exception as e:
                msg = f"❌ خطأ أثناء الاستيراد: {str(e)}"
            return redirect(f"/admin?password={ADMIN_PASSWORD}&library={selected_library}&city={selected_city}&msg={urllib.parse.quote(msg)}")

    # بناء الاستعلام
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    
    if selected_library:
        query += " AND library = ?"
        params.append(selected_library)
    if selected_city:
        query += " AND city = ?"
        params.append(selected_city)
        
    query += " ORDER BY id DESC"
    
    filtered_count = conn.execute(query.replace("SELECT *", "SELECT COUNT(*)"), params).fetchone()[0]
    total_pages = (filtered_count + per_page - 1) // per_page if filtered_count > 0 else 1
    
    query += f" LIMIT {per_page} OFFSET {(page - 1) * per_page}"
    books_list = [dict(row) for row in conn.execute(query, params).fetchall()]
    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
      <meta charset="UTF-8">
      <title>لوحة التحكم – المكتبة الجامعة</title>
      <style>
        :root { --bg:#0f172a; --panel:rgba(30,41,59,0.7); --border:rgba(255,255,255,0.1); --text:#e2e8f0; --accent:#fbbf24; --primary:#2563eb; --danger:#ef4444; --success:#10b981; }
        body { background:var(--bg); color:var(--text); font-family:sans-serif; padding:20px; margin:0; }
        h1, h2, h3 { color:var(--accent); margin-top:0; }
        a { text-decoration:none; color:inherit; }
        
        .glass { background:var(--panel); backdrop-filter:blur(10px); border:1px solid var(--border); border-radius:16px; padding:20px; box-shadow:0 4px 6px rgba(0,0,0,0.1); }
        
        .top-bar { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:15px; margin-bottom:20px; }
        .stats-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:15px; margin-bottom:20px; }
        .stat-card { text-align:center; padding:15px; border-radius:12px; background:rgba(255,255,255,0.05); }
        .stat-card h4 { margin:0 0 5px 0; color:#cbd5e1; font-size:0.9em; }
        .stat-card .num { font-size:1.8em; font-weight:bold; color:var(--accent); }
        
        .main-layout { display:flex; gap:20px; flex-wrap:wrap; align-items:flex-start; }
        .sidebar { flex:0 0 250px; display:flex; flex-direction:column; gap:20px; }
        .content { flex:1; min-width:0; }
        
        .filter-list { max-height:400px; overflow-y:auto; padding-right:5px; }
        .filter-list::-webkit-scrollbar { width:6px; }
        .filter-list::-webkit-scrollbar-thumb { background:var(--primary); border-radius:3px; }
        
        .nav-item { display:flex; align-items:center; gap:10px; padding:10px; border-radius:10px; margin-bottom:5px; transition:0.2s; }
        .nav-item:hover { background:rgba(255,255,255,0.1); }
        .nav-item.active { background:var(--primary); color:white; }
        
        input, select, button { width:100%; padding:10px; border-radius:8px; border:1px solid var(--border); background:rgba(15,23,42,0.8); color:white; outline:none; font-family:inherit; box-sizing:border-box; margin-bottom:10px; }
        input:focus, select:focus { border-color:var(--primary); }
        
        button { cursor:pointer; font-weight:bold; background:var(--primary); border:none; transition:0.2s; }
        button:hover { filter:brightness(1.1); }
        button.danger { background:var(--danger); }
        button.success { background:var(--success); }
        
        table { width:100%; border-collapse:collapse; font-size:0.9em; margin-top:15px; }
        th, td { padding:12px; text-align:right; border-bottom:1px solid var(--border); }
        th { color:var(--accent); background:rgba(0,0,0,0.2); }
        tr:hover { background:rgba(255,255,255,0.02); }
        
        .actions { display:flex; gap:5px; }
        .actions button { padding:6px 10px; font-size:0.85em; margin:0; width:auto; }
        
        .pagination { display:flex; gap:5px; justify-content:center; margin-top:20px; flex-wrap:wrap; }
        .pagination a { padding:8px 12px; background:var(--panel); border:1px solid var(--border); border-radius:8px; }
        .pagination a.active { background:var(--primary); border-color:var(--primary); }
        
        #msg-box { display:none; padding:15px; background:var(--success); border-radius:10px; margin-bottom:20px; text-align:center; font-weight:bold; }
      </style>
    </head>
    <body>
      <div class="top-bar glass">
        <h2 style="margin:0;">📚 المكتبة الجامعة - الإدارة</h2>
        <div style="display:flex; gap:10px;">
          <a href="/" target="_blank" style="padding:10px 15px; background:rgba(255,255,255,0.1); border-radius:8px;">🌍 عرض الموقع</a>
          <a href="/backup?password={{ admin_password }}" style="padding:10px 15px; background:var(--success); border-radius:8px;">🗃️ نسخة احتياطية</a>
          <a href="/export_excel?password={{ admin_password }}&mode=all" style="padding:10px 15px; background:var(--primary); border-radius:8px;">📥 تصدير الكل</a>
        </div>
      </div>
      
      <div id="msg-box"></div>

      <div class="stats-grid glass">
        <div class="stat-card"><h4>إجمالي الكتب</h4><div class="num">{{ total_books }}</div></div>
        <div class="stat-card"><h4>إجمالي المكتبات</h4><div class="num">{{ total_libraries }}</div></div>
        <div class="stat-card"><h4>إجمالي المدن</h4><div class="num">{{ total_cities }}</div></div>
        <div class="stat-card"><h4>دور النشر</h4><div class="num">{{ total_publishers }}</div></div>
      </div>

      <div class="main-layout">
        <!-- الشريط الجانبي الفلاتر -->
        <div class="sidebar">
          <div class="glass">
            <h3>🏛 المكتبات</h3>
            <a href="/admin?password={{ admin_password }}&city={{ selected_city }}" class="nav-item {{ 'active' if not selected_library else '' }}">📋 الكل</a>
            <div class="filter-list">
              {% for lib in libraries %}
              <a href="/admin?password={{ admin_password }}&library={{ lib.name }}&city={{ selected_city }}" class="nav-item {{ 'active' if selected_library == lib.name else '' }}">
                <span>{{ lib.name }}</span>
              </a>
              {% endfor %}
            </div>
          </div>
          <div class="glass">
            <h3>📍 المدن</h3>
            <a href="/admin?password={{ admin_password }}&library={{ selected_library }}" class="nav-item {{ 'active' if not selected_city else '' }}">📋 الكل</a>
            <div class="filter-list" style="max-height:200px;">
              {% for city in city_names %}
              <a href="/admin?password={{ admin_password }}&city={{ city }}&library={{ selected_library }}" class="nav-item {{ 'active' if selected_city == city else '' }}">
                <span>{{ city }}</span>
              </a>
              {% endfor %}
            </div>
          </div>
          <div class="glass">
            <h3>📱 واتساب المكتبات</h3>
            <form id="librarySettingsForm" onsubmit="saveLibrarySettings(event)">
              <select id="wa_library" style="margin-bottom:8px;">
                {% for lib in libraries %}
                <option value="{{ lib.name }}">{{ lib.name }}</option>
                {% endfor %}
              </select>
              <input id="wa_number" placeholder="رقم واتساب (مثل 905xxxxxxxxx)" style="margin-bottom:8px;">
              <input id="loc_link" placeholder="رابط خرائط جوجل" style="margin-bottom:8px;">
              <textarea id="lib_desc" placeholder="وصف المكتبة / مبيعاتها" style="width:100%; height:60px; padding:10px; border-radius:8px; border:1px solid var(--border); background:rgba(15,23,42,0.8); color:white; outline:none; margin-bottom:8px; resize:none;"></textarea>
              <button type="submit" class="success" style="font-size:0.85em;">💾 حفظ الإعدادات</button>
            </form>
            <div id="wa-msg" style="font-size:0.8em; color:var(--success); margin-top:5px;"></div>
          </div>
        </div>

        <div class="content">
          <!-- الإضافة والاستيراد -->
          <div style="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:20px;">
            <div class="glass" style="flex:1; min-width:300px;">
              <h3>➕ إضافة كتاب واحد</h3>
              <form method="POST">
                <input type="hidden" name="action" value="add">
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                  <input name="book_name" placeholder="اسم الكتاب" required style="grid-column:span 2">
                  <input name="library" placeholder="المكتبة">
                  <input name="city" placeholder="المدينة">
                  <input name="publisher" placeholder="دار النشر">
                  <input name="price" placeholder="السعر">
                  <input type="hidden" name="isbn" value="">
                  <input name="cover_image" placeholder="رابط الغلاف" style="grid-column:span 2">
                </div>
                <button type="submit">إضافة الكتاب</button>
              </form>
            </div>
            
            <div class="glass" style="flex:1; min-width:300px;">
              <h3>📁 استيراد جماعي ذكي (Excel/CSV)</h3>
              <form method="POST" enctype="multipart/form-data">
                <input type="file" name="file" accept=".xlsx,.xls,.csv" required>
                <div style="display:flex; gap:10px;">
                  <select name="target_library">
                    <option value="">-- ربط بمكتبة موجودة --</option>
                    {% for lib in libraries %}
                    <option value="{{ lib.name }}">{{ lib.name }}</option>
                    {% endfor %}
                  </select>
                  <input type="text" name="new_library" placeholder="أو مكتبة جديدة">
                </div>
                <button type="submit" class="success">استيراد الملف</button>
              </form>
              <p style="font-size:0.8em; color:#94a3b8; margin-top:10px;">الأعمدة المطلوبة: book_name, city, library, price, publisher, cover_image</p>
            </div>
          </div>

          <!-- جدول الكتب -->
          <div class="glass">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
              <div>
                <h3 style="margin:0;">📖 قائمة الكتب ({{ filtered_count }})</h3>
                <span style="font-size:0.9em; color:#94a3b8;">عرض الصفحة {{ page }} من {{ total_pages }}</span>
              </div>
              <div style="display:flex; gap:10px;">
                {% if selected_library or selected_city %}
                <a href="/export_excel?password={{ admin_password }}&mode=library&library={{ selected_library }}&city={{ selected_city }}" style="padding:10px 15px; background:rgba(255,255,255,0.1); border-radius:8px; font-size:0.9em;">📥 تصدير المعروض</a>
                {% endif %}
                <button class="danger" onclick="bulkDelete()" style="width:auto; padding:10px 15px;">🗑️ حذف المحدد</button>
              </div>
            </div>
            
            <div style="overflow-x:auto;">
              <table id="booksTable">
                <thead>
                  <tr>
                    <th style="width:30px;"><input type="checkbox" id="selectAll" onclick="toggleAll(this)"></th>
                    <th>ID</th><th>صورة</th><th>اسم الكتاب</th><th>المكتبة</th><th>المدينة</th><th>الناشر</th><th>السعر</th><th>إجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {% for b in books %}
                  <tr id="row-{{ b.id }}">
                    <td><input type="checkbox" class="row-checkbox" value="{{ b.id }}"></td>
                    <td>{{ b.id }}</td>
                    <td><img src="{{ b.cover_image or '/static/no-cover.png' }}" style="width:40px; height:50px; object-fit:cover; border-radius:4px;"></td>
                    <td class="name">{{ b.book_name }}</td>
                    <td class="lib">{{ b.library }}</td>
                    <td class="city">{{ b.city }}</td>
                    <td class="pub">{{ b.publisher }}</td>
                    <td class="price">{{ b.price }}</td>
                    <td class="isbn" style="display:none">{{ b.isbn }}</td>
                    <td class="actions">
                      <button onclick="editBook({{ b.id }})">✏️</button>
                      <button class="danger" onclick="deleteBook({{ b.id }})">🗑️</button>
                    </td>
                  </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
            
            <!-- أزرار الصفحات -->
            {% if total_pages > 1 %}
            <div class="pagination">
              {% if page > 1 %}
              <a href="/admin?password={{ admin_password }}&library={{ selected_library }}&city={{ selected_city }}&page={{ page - 1 }}">السابق</a>
              {% endif %}
              
              {% set start_page = page - 2 if page > 2 else 1 %}
              {% set end_page = page + 2 if page + 2 < total_pages else total_pages %}
              
              {% for p in range(start_page, end_page + 1) %}
              <a href="/admin?password={{ admin_password }}&library={{ selected_library }}&city={{ selected_city }}&page={{ p }}" class="{{ 'active' if p == page else '' }}">{{ p }}</a>
              {% endfor %}
              
              {% if page < total_pages %}
              <a href="/admin?password={{ admin_password }}&library={{ selected_library }}&city={{ selected_city }}&page={{ page + 1 }}">التالي</a>
              {% endif %}
            </div>
            {% endif %}
          </div>
        </div>
      </div>

      <!-- نافذة التعديل -->
      <div id="editModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; justify-content:center; align-items:center;">
        <div class="glass" style="width:90%; max-width:500px; position:relative;">
          <h3 style="margin-bottom:20px;">✏️ تعديل كتاب</h3>
          <form id="editForm">
            <input type="hidden" id="edit_id" name="id">
            <input id="edit_name" name="book_name" placeholder="اسم الكتاب" required>
            <input id="edit_library" name="library" placeholder="المكتبة">
            <input id="edit_city" name="city" placeholder="المدينة">
            <input id="edit_publisher" name="publisher" placeholder="دار النشر">
            <input id="edit_price" name="price" placeholder="السعر">
            <input type="hidden" id="edit_isbn" name="isbn" value="">
            <input id="edit_cover" name="cover_image" placeholder="رابط صورة الغلاف">
            <div style="display:flex; gap:10px; margin-top:15px;">
              <button type="button" class="success" onclick="submitEdit()">حفظ التعديلات</button>
              <button type="button" class="danger" onclick="document.getElementById('editModal').style.display='none'">إلغاء</button>
            </div>
          </form>
        </div>
      </div>

      <script>
        const ADMIN_PASSWORD = "{{ admin_password }}";
        
        // إظهار الرسائل القادمة من الرابط
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('msg')) {
            const msgBox = document.getElementById('msg-box');
            msgBox.textContent = decodeURIComponent(urlParams.get('msg'));
            msgBox.style.display = 'block';
            setTimeout(() => msgBox.style.display = 'none', 5000);
            
            // إزالة msg من الرابط حتى لا تظهر عند التحديث
            urlParams.delete('msg');
            window.history.replaceState(null, '', '?' + urlParams.toString());
        }

        function toggleAll(source) {
            let checkboxes = document.querySelectorAll('.row-checkbox');
            for(let i=0; i<checkboxes.length; i++) {
                checkboxes[i].checked = source.checked;
            }
        }
        
        function bulkDelete() {
            let checkboxes = document.querySelectorAll('.row-checkbox:checked');
            let ids = Array.from(checkboxes).map(cb => cb.value);
            if(ids.length === 0) return alert("الرجاء تحديد كتاب واحد على الأقل.");
            
            if (confirm("هل أنت متأكد من حذف " + ids.length + " كتاب نهائياً؟")) {
                let formData = new FormData();
                formData.append("action", "bulk_delete");
                ids.forEach(id => formData.append("ids[]", id));
                
                fetch("/admin?password=" + ADMIN_PASSWORD, {
                    method: "POST", body: formData
                }).then(res => res.json()).then(data => {
                    alert(data.msg);
                    location.reload();
                }).catch(err => alert("حدث خطأ"));
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
            document.getElementById("editModal").style.display = "flex";
        }

        function submitEdit() {
            let form = document.getElementById("editForm");
            let formData = new FormData(form);
            formData.append("action", "edit");
            fetch("/admin?password=" + ADMIN_PASSWORD, {
                method: "POST", body: formData
            }).then(res => res.json()).then(data => {
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
                    method: "POST", body: formData
                }).then(res => res.json()).then(data => {
                    alert(data.msg);
                    location.reload();
                }).catch(err => alert("خطأ"));
            }
        }

        function saveLibrarySettings(e) {
            e.preventDefault();
            let formData = new FormData();
            formData.append("password", ADMIN_PASSWORD);
            formData.append("library_name", document.getElementById("wa_library").value);
            formData.append("whatsapp_number", document.getElementById("wa_number").value);
            formData.append("location_link", document.getElementById("loc_link").value);
            formData.append("description", document.getElementById("lib_desc").value);
            fetch("/save_library_settings", {
                method: "POST", body: formData
            }).then(res => res.json()).then(data => {
                document.getElementById("wa-msg").textContent = data.msg;
                setTimeout(() => document.getElementById("wa-msg").textContent = '', 3000);
            }).catch(err => alert("خطأ"));
        }
      </script>
    </body>
    </html>
    """, books=books_list, total_books=total_books, total_libraries=total_libraries, 
    total_cities=total_cities, total_publishers=total_publishers, 
    libraries=libraries, city_names=city_names,
    selected_library=selected_library, selected_city=selected_city,
    page=page, total_pages=total_pages, filtered_count=filtered_count,
    admin_password=ADMIN_PASSWORD)

@app.route("/", defaults={'path': ''})
@app.route("/<path:path>")
def serve_nextjs(path):
    # لا تتدخل في مسارات API التي قد تسبق هذا المسار
    full_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.isfile(full_path):
        return send_file(full_path)
    elif path != "" and os.path.isfile(f"{full_path}.html"):
        return send_file(f"{full_path}.html")
    elif path != "" and os.path.isfile(os.path.join(full_path, "index.html")):
        return send_file(os.path.join(full_path, "index.html"))
    else:
        return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route("/search")
def api():
    q = request.args.get("q", "")
    library = request.args.get("library", "")
    return jsonify(search(q, library))

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
    books = conn.execute(
        """SELECT b.*, COALESCE(ls.whatsapp_number, '') as whatsapp_number
           FROM books b LEFT JOIN library_settings ls ON b.library = ls.library_name
           ORDER BY b.id DESC LIMIT 1000"""
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in books])

@app.route("/bookstores_data")
def bookstores_data():
    conn = get_db()
    rows = conn.execute("""
        SELECT b.library, b.city, COUNT(*) as books_count,
               COALESCE(ls.whatsapp_number, '') as whatsapp_number,
               COALESCE(ls.location_link, '') as location_link,
               COALESCE(ls.description, '') as description
        FROM books b
        LEFT JOIN library_settings ls ON b.library = ls.library_name
        WHERE b.library != ''
        GROUP BY b.library
        ORDER BY books_count DESC
    """).fetchall()
    conn.close()
    result = []
    for row in rows:
        lib_name = row[0]
        safe_name = lib_name.replace(' ', '_')
        logo_url = None
        for ext in ['png', 'jpg', 'jpeg']:
            logo_path = f'logos/{safe_name}.{ext}'
            full_path = os.path.join(app.static_folder, logo_path)
            if os.path.exists(full_path):
                logo_url = '/' + urllib.parse.quote(logo_path)
                break
        result.append({
            'name': lib_name,
            'city': row[1],
            'books_count': row[2],
            'whatsapp_number': row[3],
            'location_link': row[4],
            'description': row[5],
            'logo': logo_url
        })
    return jsonify(result)

@app.route("/save_library_settings", methods=["POST"])
def save_library_settings():
    if request.form.get("password") != ADMIN_PASSWORD:
        return jsonify({"status": "error", "msg": "غير مصرح"}), 403
    library_name = request.form.get("library_name", "").strip()
    whatsapp_number = request.form.get("whatsapp_number", "").strip()
    location_link = request.form.get("location_link", "").strip()
    description = request.form.get("description", "").strip()
    if not library_name:
        return jsonify({"status": "error", "msg": "اسم المكتبة مطلوب"}), 400
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO library_settings (library_name, whatsapp_number, location_link, description) VALUES (?, ?, ?, ?)",
        (library_name, whatsapp_number, location_link, description)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "msg": f"تم حفظ إعدادات {library_name}"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
