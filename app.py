from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ========== دالة محاولة استخراج رابط Goodreads المباشر ==========
def get_goodreads_book_url(book_title):
    """يبحث في Goodreads عن الكتاب ويعيد رابط الصفحة الأولى المطابقة"""
    search_url = f"https://www.goodreads.com/search?q={requests.utils.quote(book_title)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(search_url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        # نجد أول عنصر رابط لكتاب في نتائج البحث
        book_link = soup.select_one("a.bookTitle")
        if book_link and book_link.get("href"):
            return "https://www.goodreads.com" + book_link["href"]
    except Exception as e:
        print(f"Goodreads scraping error: {e}")
    return None

# ========== راوت يعطي رابط Goodreads مباشر ==========
@app.route("/go_goodreads")
def go_goodreads():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "No query"}), 400

    direct_url = get_goodreads_book_url(q)
    if direct_url:
        return jsonify({"url": direct_url})
    # fallback: صفحة البحث العادية
    return jsonify({"url": f"https://www.goodreads.com/search?q={requests.utils.quote(q)}"})

# ========== البحث في Excel ==========
def search(book):
    df = pd.read_excel("books.xlsx")
    df = df.fillna("")
    result = df[df["book_name"].str.contains(book, case=False, na=False)]
    return result.to_dict(orient="records")

# ========== واجهة المستخدم ==========
HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>مكتبة الكتب</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #0f172a; color: #e2e8f0; }
    .container { max-width: 950px; margin: auto; padding: 20px; }
    h1 { text-align: center; color: #fbbf24; margin-bottom: 25px; font-size: 2em; }

    .search-box { margin-bottom: 20px; }
    input {
      width: 100%; padding: 14px 18px; border-radius: 14px;
      border: 1px solid #334155; background: #1e293b; color: white; font-size: 16px;
    }
    input:focus { outline: none; border-color: #38bdf8; }

    .filters { display: flex; gap: 12px; margin-bottom: 25px; flex-wrap: wrap; }
    select {
      padding: 10px 16px; border-radius: 12px; border: 1px solid #334155;
      background: #1e293b; color: white; font-size: 14px; cursor: pointer;
    }

    .city-card {
      background: linear-gradient(145deg, #1e293b, #0f172a);
      margin-top: 18px; padding: 18px; border-radius: 18px;
      border: 1px solid #334155; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .city-name { font-size: 1.4em; color: #38bdf8; margin-bottom: 12px; }
    .library-name { color: #fbbf24; font-weight: bold; margin: 15px 0 10px; font-size: 1.2em; }

    .books-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px;
      margin-right: 15px;
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

    /* Modal */
    .modal {
      display: none; position: fixed; z-index: 1000;
      left: 0; top: 0; width: 100%; height: 100%; overflow: auto;
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
    .modal-book-header img {
      width: 150px; height: 220px; object-fit: cover; border-radius: 12px;
      border: 1px solid #334155;
    }
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
      text-decoration: none; font-size: 1em; text-align: center;
      transition: background 0.2s; cursor: pointer;
    }
    .goodreads-btn:hover { background: #4a2c1a; }

    .googlebooks-btn {
      background: #2563eb; color: white;
    }
    .googlebooks-btn:hover { background: #1d4ed8; }

    .share-btn {
      display: inline-block; margin-top: 10px; padding: 10px 20px;
      background: #334155; color: white; border-radius: 10px;
      cursor: pointer; border: none; font-size: 1em;
    }
    .share-btn:hover { background: #475569; }

    @media (max-width: 600px) {
      .modal-book-header { flex-direction: column; align-items: center; text-align: center; }
      .modal-book-header img { width: 180px; height: 260px; }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>📚 محرك بحث الكتب</h1>
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="اكتب اسم الكتاب..." autocomplete="off">
    </div>
    <div class="filters">
      <select id="sortBy">
        <option value="">🔃 ترتيب حسب</option>
        <option value="price_asc">السعر: من الأقل إلى الأعلى</option>
        <option value="price_desc">السعر: من الأعلى إلى الأقل</option>
      </select>
      <select id="cityFilter"><option value="">🏙️ كل المدن</option></select>
    </div>
    <div id="results"></div>
  </div>

  <!-- Modal -->
  <div id="bookModal" class="modal">
    <div class="modal-content">
      <span class="close" onclick="closeModal()">&times;</span>
      <div id="modalBody"></div>
    </div>
  </div>

  <script>
    let currentResults = [];
    const resultsDiv = document.getElementById('results');
    const modal = document.getElementById('bookModal');

    // بحث مباشر
    let debounceTimer;
    document.getElementById('searchInput').addEventListener('input', function() {
      clearTimeout(debounceTimer);
      const query = this.value.trim();
      if (query.length < 2) { currentResults = []; resultsDiv.innerHTML = ''; updateCityFilter([]); return; }
      debounceTimer = setTimeout(() => {
        fetch(`/search?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => { currentResults = data; updateCityFilter(data); applyFiltersAndRender(); })
          .catch(err => { console.error(err); resultsDiv.innerHTML = '<div class="no-results">⚠️ خطأ في الاتصال</div>'; });
      }, 300);
    });

    function applyFiltersAndRender() {
      let filtered = [...currentResults];
      const city = document.getElementById('cityFilter').value;
      if (city) filtered = filtered.filter(b => b.city === city);
      const sort = document.getElementById('sortBy').value;
      if (sort === 'price_asc') filtered.sort((a,b) => parseFloat(a.price) - parseFloat(b.price));
      else if (sort === 'price_desc') filtered.sort((a,b) => parseFloat(b.price) - parseFloat(a.price));
      renderResults(filtered);
    }

    function updateCityFilter(data) {
      const cities = [...new Set(data.map(b => b.city).filter(c => c))];
      const select = document.getElementById('cityFilter');
      select.innerHTML = '<option value="">🏙️ كل المدن</option>';
      cities.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; select.appendChild(o); });
    }

    document.getElementById('sortBy').addEventListener('change', applyFiltersAndRender);
    document.getElementById('cityFilter').addEventListener('change', applyFiltersAndRender);

    function renderResults(books) {
      if (books.length === 0) { resultsDiv.innerHTML = '<div class="no-results">🔍 لا توجد نتائج</div>'; return; }
      const grouped = {};
      books.forEach(b => {
        const city = b.city || 'غير معروف', lib = b.library || 'مكتبة غير محددة';
        if (!grouped[city]) grouped[city] = {};
        if (!grouped[city][lib]) grouped[city][lib] = [];
        grouped[city][lib].push(b);
      });
      let html = '';
      for (const city in grouped) {
        html += `<div class="city-card"><div class="city-name">📍 ${city}</div>`;
        for (const lib in grouped[city]) {
          html += `<div class="library-name">🏛 ${lib}</div><div class="books-grid">`;
          grouped[city][lib].forEach(book => {
            const img = book.cover_image || 'https://via.placeholder.com/80x110/1e293b/94a3b8?text=No+Cover';
            html += `
              <div class="book-card" onclick="openBookModal('${encodeURIComponent(book.book_name || '')}')">
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
      resultsDiv.innerHTML = html;
    }

    // فتح النافذة المنبثقة
    function openBookModal(encodedName) {
      const bookName = decodeURIComponent(encodedName);
      const book = currentResults.find(b => b.book_name === bookName);
      if (!book) return;

      const body = document.getElementById('modalBody');
      const imgSrc = book.cover_image || 'https://via.placeholder.com/150x220/1e293b/94a3b8?text=No+Cover';

      // رابط Google Books الاحتياطي
      const googleBooksSearchUrl = `https://www.google.com/search?tbm=bks&q=${encodeURIComponent(bookName)}`;

      body.innerHTML = `
        <div class="modal-book-header">
          <img src="${imgSrc}" alt="${bookName}">
          <div class="modal-book-info">
            <h2>${bookName}</h2>
            <p>📘 الناشر: ${book.publisher || 'غير معروف'}</p>
            <p>🏛 المكتبة: ${book.library || 'غير محددة'}</p>
            <p>📍 المدينة: ${book.city || 'غير محددة'}</p>
            <p class="price">💰 السعر: ${book.price || 'غير متوفر'}</p>

            <div class="rating-section">
              <div class="goodreads-btn" onclick="openGoodreads('${encodeURIComponent(bookName)}')">
                📊 تقييمات ومراجعات Goodreads
              </div>
              <a href="${googleBooksSearchUrl}" target="_blank" class="googlebooks-btn">
                📖 آراء Google Books
              </a>
            </div>

            <button class="share-btn" onclick="shareBook('${bookName}')">📤 مشاركة الكتاب</button>
          </div>
        </div>
      `;

      modal.style.display = 'block';
    }

    // دالة جديدة تطلب الرابط المباشر ثم تفتحه
    function openGoodreads(encodedBookName) {
      const bookName = decodeURIComponent(encodedBookName);
      fetch(`/go_goodreads?q=${encodeURIComponent(bookName)}`)
        .then(res => res.json())
        .then(data => {
          if (data.url) {
            window.open(data.url, '_blank');
          } else {
            // fallback
            window.open(`https://www.goodreads.com/search?q=${encodeURIComponent(bookName)}`, '_blank');
          }
        })
        .catch(() => {
          window.open(`https://www.goodreads.com/search?q=${encodeURIComponent(bookName)}`, '_blank');
        });
    }

    function shareBook(bookName) {
      const text = `📚 أنصحك بقراءة هذا الكتاب: "${bookName}"`;
      if (navigator.share) {
        navigator.share({ title: 'مشاركة كتاب', text: text }).catch(()=>{});
      } else {
        navigator.clipboard.writeText(text).then(() => alert('تم نسخ اسم الكتاب!')).catch(() => prompt('انسخ اسم الكتاب:', text));
      }
    }

    function closeModal() { modal.style.display = 'none'; }
    window.onclick = function(event) { if (event.target == modal) closeModal(); }
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

if __name__ == "__main__":
    app.run(port=5000, debug=True)