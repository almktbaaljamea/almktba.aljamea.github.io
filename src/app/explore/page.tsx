"use client";

import BookCard from '@/components/BookCard';
import SearchBar from '@/components/SearchBar';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import './search.css';

function ExploreContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';

  const [books, setBooks] = useState<any[]>([]);
  const [filtersData, setFiltersData] = useState<any>({ cities: [], libraries: [], publishers: [], min_price: 0, max_price: 0 });
  const [loading, setLoading] = useState(true);
  const [selectedBook, setSelectedBook] = useState<any>(null);

  // Filter States
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [selectedCities, setSelectedCities] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  useEffect(() => {
    fetch('/filters_data').then(res => res.json()).then(data => setFiltersData(data)).catch(console.error);

    setLoading(true);
    const endpoint = query.length >= 2 ? `/search?q=${encodeURIComponent(query)}` : `/initial_books`;
    
    fetch(endpoint)
      .then(res => res.json())
      .then(data => {
        setBooks(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [query]);

  const handleCityToggle = (city: string) => {
    setSelectedCities(prev => prev.includes(city) ? prev.filter(c => c !== city) : [...prev, city]);
  };

  const handleCategoryToggle = (pub: string) => {
    setSelectedCategories(prev => prev.includes(pub) ? prev.filter(c => c !== pub) : [...prev, pub]);
  };

  const filteredBooks = books.filter(b => {
    if (selectedCities.length > 0 && !selectedCities.includes(b.city)) return false;
    if (selectedCategories.length > 0 && !selectedCategories.includes(b.publisher)) return false;
    return true;
  });

  const handleOpenGoodreads = (bookName: string) => {
    const searchUrl = `https://duckduckgo.com/?q=!ducky+site:goodreads.com/book/show+${encodeURIComponent(bookName)}`;
    window.open(searchUrl, '_blank');
  };

  const handleWhatsApp = (book: any) => {
    if (!book.whatsapp_number) {
      alert('رقم واتساب هذه المكتبة غير متوفر حالياً');
      return;
    }
    const message = `السلام عليكم، أنا أتيت من منصة المكتبة الجامعة وأرغب في شراء كتاب: ${book.book_name}`;
    const url = `https://wa.me/${book.whatsapp_number}?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
  };

  return (
    <div className="search-page container">
      {loading && (
        <div className="loader-overlay" style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15,23,42,0.8)', zIndex: 9999, display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
          <div style={{color: '#fbbf24', fontSize: '1.5em'}}>جاري التحميل...</div>
        </div>
      )}

      <div className="search-header animate-fade-in">
        <h1 className="title-main">نتائج البحث</h1>
        <p className="subtitle">
          {query ? `نتائج البحث عن: "${query}"` : 'تصفح جميع الكتب المتوفرة في المكتبات العربية'}
        </p>
        <div className="search-bar-wrapper">
          <SearchBar placeholder="ابحث عن كتاب آخر..." />
        </div>
      </div>

      <div className="search-content">
        <button className="mobile-filter-btn" onClick={() => setIsFilterOpen(true)}>
          🔍 تصفية النتائج
        </button>
        <div className={`sidebar-overlay ${isFilterOpen ? 'open' : ''}`} onClick={() => setIsFilterOpen(false)}></div>
        
        <aside className={`search-sidebar glass-panel animate-fade-in animate-delay-1 ${isFilterOpen ? 'open' : ''}`}>
          <button className="close-sidebar-btn" onClick={() => setIsFilterOpen(false)}>&times;</button>
          <h3 className="filter-title">تصفية النتائج</h3>
          
          <div className="filter-group">
            <h4 className="filter-subtitle">المدينة</h4>
            {filtersData.cities.map((city: string) => (
              <label key={city} className="filter-label">
                <input type="checkbox" checked={selectedCities.includes(city)} onChange={() => handleCityToggle(city)} /> {city}
              </label>
            ))}
          </div>

          <div className="filter-group">
            <h4 className="filter-subtitle">دار النشر</h4>
            {filtersData.publishers.map((pub: string) => (
              <label key={pub} className="filter-label">
                <input type="checkbox" checked={selectedCategories.includes(pub)} onChange={() => handleCategoryToggle(pub)} /> {pub}
              </label>
            ))}
          </div>
        </aside>

        <div className="search-results">
          <p style={{marginBottom: '20px', color: '#94a3b8'}}>تم العثور على <strong>{filteredBooks.length}</strong> كتاب</p>
          <div className="books-grid">
            {filteredBooks.map((book, index) => (
              <div key={book.id} className={`animate-fade-in animate-delay-${(index % 3) + 1}`}>
                <BookCard {...book} onOpenModal={() => setSelectedBook(book)} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedBook && (
        <div className="book-modal-overlay" onClick={() => setSelectedBook(null)}>
          <div className="book-modal-content" onClick={e => e.stopPropagation()}>
            <div className="book-modal-close" onClick={() => setSelectedBook(null)}>&times;</div>
            
            <div className="book-modal-image-wrapper">
              <img src={selectedBook.cover_image || '/static/no-cover.png'} alt={selectedBook.book_name} className="book-modal-image" />
            </div>
            
            <div className="book-modal-info">
              <h2 className="book-modal-title">{selectedBook.book_name}</h2>
              <div className="book-modal-author">الناشر: {selectedBook.publisher || 'غير معروف'}</div>
              
              <div className="book-modal-details-grid">
                <div className="detail-item">
                  <span className="detail-label">🏛 المكتبة</span>
                  <span className="detail-value">{selectedBook.library || 'غير محددة'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">📍 المدينة</span>
                  <span className="detail-value">{selectedBook.city || 'غير محددة'}</span>
                </div>
              </div>
              
              <div className="book-modal-price">
                {selectedBook.price || 'غير متوفر'} <span>سعر البيع</span>
              </div>
              
              <div className="book-modal-actions">
                <button className="action-btn btn-whatsapp" onClick={() => handleWhatsApp(selectedBook)}>
                  💬 تواصل مع المكتبة
                </button>
                <button className="action-btn btn-goodreads" onClick={() => handleOpenGoodreads(selectedBook.book_name)}>
                  📊 تقييمات Goodreads
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="container" style={{padding: '100px 20px', textAlign: 'center'}}>جاري التحميل...</div>}>
      <ExploreContent />
    </Suspense>
  );
}

