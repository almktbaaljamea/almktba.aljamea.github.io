"use client";

import Link from 'next/link';
import { useEffect, useState } from 'react';
import './bookstores.css';

interface LibraryData {
  name: string;
  city: string;
  books_count: number;
  whatsapp_number: string;
  logo: string | null;
}

export default function BookstoresDirectory() {
  const [stores, setStores] = useState<LibraryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCity, setSelectedCity] = useState('');

  useEffect(() => {
    fetch('/bookstores_data')
      .then(res => res.json())
      .then(data => {
        setStores(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const cities = [...new Set(stores.map(s => s.city).filter(Boolean))];
  const filteredStores = selectedCity ? stores.filter(s => s.city === selectedCity) : stores;

  return (
    <div className="bookstores-page container">
      <div className="page-header animate-fade-in">
        <h1 className="title-main">دليل المكتبات العربية</h1>
        <p className="subtitle">تعرف على المكتبات العربية المشتركة لدينا وعدد الكتب المتوفرة في كل مكتبة</p>
      </div>

      {loading ? (
        <div style={{textAlign: 'center', padding: '60px 0', color: 'var(--text-light)'}}>
          <div style={{fontSize: '2rem', marginBottom: '10px'}}>📚</div>
          جاري تحميل دليل المكتبات...
        </div>
      ) : (
        <>
          <div className="city-filters animate-fade-in animate-delay-1">
            <button className={`btn ${!selectedCity ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setSelectedCity('')}>الكل ({stores.length})</button>
            {cities.map(city => (
              <button
                key={city}
                className={`btn ${selectedCity === city ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedCity(city)}
              >
                {city} ({stores.filter(s => s.city === city).length})
              </button>
            ))}
          </div>

          <div className="stores-grid">
            {filteredStores.map((store, index) => (
              <div key={store.name} className={`store-card glass-panel animate-fade-in animate-delay-${(index % 3) + 1}`}>
                <div className="store-header">
                  <div className="store-avatar">
                    {store.logo ? (
                      <img src={store.logo} alt={store.name} style={{width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%'}} />
                    ) : (
                      '🏢'
                    )}
                  </div>
                  <div>
                    <h3 className="store-name">{store.name}</h3>
                    <span className="store-city">📍 {store.city || 'غير محددة'}</span>
                  </div>
                </div>
                <div className="store-details">
                  <p><strong>الكتب المتوفرة:</strong> {store.books_count} كتاب</p>
                  {store.whatsapp_number && (
                    <p><strong>واتساب:</strong> <a href={`https://wa.me/${store.whatsapp_number}`} target="_blank" rel="noopener noreferrer" style={{color: '#25D366'}}>تواصل معنا 💬</a></p>
                  )}
                </div>
                <div className="store-footer">
                  <span className="store-rating">📚 {store.books_count}+ كتاب</span>
                  <Link href={`/explore?q=`} className="btn btn-secondary btn-sm">تصفح الكتب</Link>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
