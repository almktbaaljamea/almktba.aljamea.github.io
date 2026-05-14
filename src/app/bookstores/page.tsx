import Link from 'next/link';
import './bookstores.css';

export default function BookstoresDirectory() {
  const stores = [
    { id: 1, name: 'مكتبة اقرأ', city: 'إسطنبول', address: 'الفاتح، شارع فوزي باشا', booksCount: 1250, rating: 4.8 },
    { id: 2, name: 'مكتبة الفاتح', city: 'إسطنبول', address: 'الفاتح، جوار جامع الفاتح', booksCount: 980, rating: 4.5 },
    { id: 3, name: 'دار المعرفة', city: 'غازي عنتاب', address: 'شارع الجامعة', booksCount: 650, rating: 4.7 },
    { id: 4, name: 'مكتبة النور', city: 'بورصة', address: 'عثمان غازي', booksCount: 420, rating: 4.2 },
    { id: 5, name: 'مكتبة القلم', city: 'أنطاكيا', address: 'مركز المدينة', booksCount: 300, rating: 4.0 },
  ];

  return (
    <div className="bookstores-page container">
      <div className="page-header animate-fade-in">
        <h1 className="title-main">دليل المكتبات العربية</h1>
        <p className="subtitle">تعرف على المكتبات العربية في مختلف المدن التركية</p>
      </div>

      <div className="city-filters animate-fade-in animate-delay-1">
        <button className="btn btn-primary">الكل</button>
        <button className="btn btn-secondary">إسطنبول</button>
        <button className="btn btn-secondary">غازي عنتاب</button>
        <button className="btn btn-secondary">بورصة</button>
        <button className="btn btn-secondary">أنطاكيا</button>
      </div>

      <div className="stores-grid">
        {stores.map((store, index) => (
          <div key={store.id} className={`store-card glass-panel animate-fade-in animate-delay-${(index % 3) + 1}`}>
            <div className="store-header">
              <div className="store-avatar">🏢</div>
              <div>
                <h3 className="store-name">{store.name}</h3>
                <span className="store-city">📍 {store.city}</span>
              </div>
            </div>
            <div className="store-details">
              <p><strong>العنوان:</strong> {store.address}</p>
              <p><strong>الكتب المتوفرة:</strong> +{store.booksCount} كتاب</p>
            </div>
            <div className="store-footer">
              <span className="store-rating">⭐ {store.rating}</span>
              <Link href={`/search?store=${store.id}`} className="btn btn-secondary btn-sm">تصفح الكتب</Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
