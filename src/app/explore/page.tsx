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
  const [selectedCities, setSelectedCities] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]); // Publishers used as Categories for now

  useEffect(() => {
    // Fetch filter data
    fetch('/filters_data').then(res => res.json()).then(data => setFiltersData(data)).catch(console.error);

    // Fetch books
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

  // Apply Client-Side filters
  const filteredBooks = books.filter(b => {
    if (selectedCities.length > 0 && !selectedCities.includes(b.city)) return false;
    if (selectedCategories.length > 0 && !selectedCategories.includes(b.publisher)) return false;
    return true;
  });

  const handleOpenGoodreads = (bookName: string) => {
    window.open(`https://www.goodreads.com/search?q=${encodeURIComponent(bookName)}`, '_blank');
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
        <aside className="search-sidebar glass-panel animate-fade-in animate-delay-1">
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
        <div className="modal-overlay" style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', zIndex: 2000, display: 'flex', justifyContent: 'center', alignItems: 'center'}} onClick={() => setSelectedBook(null)}>
          <div className="modal-content glass-panel" style={{background: '#1e293b', padding: '25px', borderRadius: '20px', width: '90%', maxWidth: '650px', position: 'relative'}} onClick={e => e.stopPropagation()}>
            <span style={{position: 'absolute', top: '10px', left: '20px', fontSize: '30px', cursor: 'pointer', color: '#94a3b8'}} onClick={() => setSelectedBook(null)}>&times;</span>
            <div style={{display: 'flex', gap: '20px', flexWrap: 'wrap'}}>
              <img src={selectedBook.cover_image || '/static/no-cover.png'} alt={selectedBook.book_name} style={{width: '150px', height: '220px', objectFit: 'cover', borderRadius: '12px'}} />
              <div style={{flex: 1, minWidth: '250px'}}>
                <h2 style={{color: '#fbbf24', marginBottom: '8px'}}>{selectedBook.book_name}</h2>
                <p style={{color: '#cbd5e1', margin: '6px 0'}}>📘 الناشر: {selectedBook.publisher || 'غير معروف'}</p>
                <p style={{color: '#cbd5e1', margin: '6px 0'}}>🏛 المكتبة: {selectedBook.library || 'غير محددة'}</p>
                <p style={{color: '#cbd5e1', margin: '6px 0'}}>📍 المدينة: {selectedBook.city || 'غير محددة'}</p>
                <p style={{color: '#4ade80', fontSize: '1.3em', fontWeight: 'bold', margin: '10px 0'}}>💰 السعر: {selectedBook.price || 'غير متوفر'}</p>
                
                <div style={{marginTop: '15px', padding: '12px', background: '#0f172a', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '10px'}}>
                  <button onClick={() => handleOpenGoodreads(selectedBook.book_name)} style={{padding: '12px', background: '#382110', color: '#f3d9b1', borderRadius: '10px', border: 'none', cursor: 'pointer', fontSize: '1em'}}>📊 تقييمات ومراجعات Goodreads</button>
                  <a href={`https://www.google.com/search?tbm=bks&q=${encodeURIComponent(selectedBook.book_name)}`} target="_blank" style={{padding: '12px', background: '#2563eb', color: 'white', borderRadius: '10px', textDecoration: 'none', textAlign: 'center', fontSize: '1em'}}>📖 آراء Google Books</a>
                </div>
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
