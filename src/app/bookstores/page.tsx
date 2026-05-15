"use client";

import Link from 'next/link';
import { useEffect, useState } from 'react';
import './bookstores.css';

interface LibraryData {
  name: string;
  city: string;
  books_count: number;
  whatsapp_number: string;
  location_link: string;
  description: string;
  logo: string | null;
}

export default function BookstoresDirectory() {
  const [stores, setStores] = useState<LibraryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedStore, setSelectedStore] = useState<LibraryData | null>(null);

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
                  <button className="btn btn-primary btn-sm" onClick={() => setSelectedStore(store)}>المعلومات</button>
                  <Link href={`/explore?library=${encodeURIComponent(store.name)}`} className="btn btn-secondary btn-sm">تصفح الكتب</Link>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {selectedStore && (
        <div className="book-modal-overlay" onClick={() => setSelectedStore(null)}>
          <div className="book-modal-content" onClick={e => e.stopPropagation()}>
            <div className="book-modal-close" onClick={() => setSelectedStore(null)}>&times;</div>
            <div className="book-modal-info" style={{padding: '20px'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px'}}>
                <div className="store-avatar" style={{width: '80px', height: '80px', fontSize: '2rem'}}>
                  {selectedStore.logo ? <img src={selectedStore.logo} alt={selectedStore.name} style={{width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%'}} /> : '🏢'}
                </div>
                <div>
                  <h2 className="title-main" style={{margin: 0, fontSize: '1.8rem'}}>{selectedStore.name}</h2>
                  <span style={{color: '#94a3b8'}}>📍 {selectedStore.city}</span>
                </div>
              </div>
              
              <div className="glass-panel" style={{padding: '20px', marginBottom: '20px', background: 'rgba(255,255,255,0.05)'}}>
                <h4 style={{color: '#fbbf24', marginBottom: '10px'}}>وصف المكتبة</h4>
                <p style={{lineHeight: '1.6', color: '#e2e8f0'}}>{selectedStore.description || 'لا يوجد وصف متوفر حالياً لهذه المكتبة.'}</p>
              </div>

              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '30px'}}>
                <div className="glass-panel" style={{padding: '15px', textAlign: 'center'}}>
                  <div style={{fontSize: '0.9rem', color: '#94a3b8'}}>إجمالي الكتب</div>
                  <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#fbbf24'}}>{selectedStore.books_count}</div>
                </div>
                <div className="glass-panel" style={{padding: '15px', textAlign: 'center'}}>
                  <div style={{fontSize: '0.9rem', color: '#94a3b8'}}>حالة التوفر</div>
                  <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981'}}>نشط ✅</div>
                </div>
              </div>

              <div style={{display: 'flex', gap: '15px'}}>
                {selectedStore.location_link && (
                  <a href={selectedStore.location_link} target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{flex: 1, textAlign: 'center', display: 'block'}}>
                    🗺️ الموقع على الخريطة
                  </a>
                )}
                {selectedStore.whatsapp_number && (
                  <a href={`https://wa.me/${selectedStore.whatsapp_number}`} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{flex: 1, textAlign: 'center', display: 'block', background: '#25D366', color: 'white', border: 'none'}}>
                    💬 تواصل عبر واتساب
                  </a>
                )}
              </div>
              <Link href={`/explore?library=${encodeURIComponent(selectedStore.name)}`} className="btn btn-primary" style={{width: '100%', marginTop: '15px', display: 'block', textAlign: 'center', background: 'linear-gradient(to right, #2563eb, #1d4ed8)'}}>
                📚 عرض جميع كتب هذه المكتبة فقط
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
