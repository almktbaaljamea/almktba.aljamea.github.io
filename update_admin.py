import re
import urllib.parse
with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

new_admin_code = '''@app.route("/admin", methods=["GET", "POST"])
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
            return redirect(f"/admin?password={ADMIN_PASSWORD}&library={selected_library}&city={selected_city}&msg=تمت الإضافة بنجاح")

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

    html_content = """
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
                  <input name="isbn" placeholder="ISBN">
                  <input name="cover_image" placeholder="رابط الغلاف">
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
              <p style="font-size:0.8em; color:#94a3b8; margin-top:10px;">الأعمدة المطلوبة: book_name, city, library, price, publisher, cover_image, isbn</p>
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
            <input id="edit_isbn" name="isbn" placeholder="ISBN">
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
      </script>
    </body>
    </html>
    """, books=books_list, total_books=total_books, total_libraries=total_libraries, 
    total_cities=total_cities, total_publishers=total_publishers, 
    libraries=libraries, city_names=city_names,
    selected_library=selected_library, selected_city=selected_city,
    page=page, total_pages=total_pages, filtered_count=filtered_count,
    admin_password=ADMIN_PASSWORD)
'''

start_idx = content.find('@app.route("/admin", methods=["GET", "POST"])')
end_idx = content.find('@app.route("/")')

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_admin_code + '\n' + content[end_idx:]
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Done")
else:
    print("Error finding boundaries")
