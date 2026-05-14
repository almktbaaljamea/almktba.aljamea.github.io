import Link from 'next/link';
import './book.css';

export default function BookDetails({ params }: { params: { id: string } }) {
  // Mock data for the book
  const book = {
    id: params.id,
    title: 'البداية والنهاية',
    author: 'ابن كثير',
    publisher: 'دار ابن كثير',
    category: 'تاريخ',
    coverColor: '#8B4513',
    description: 'عمل موسوعي تاريخي ضخم، يتحدث عن بدء الخلق من خلق العرش والكرسي والسماوات والأرضين وقصص الأنبياء...',
  };

  // Mock data for the bookstores selling this book
  const stores = [
    { id: 1, name: 'مكتبة اقرأ', city: 'إسطنبول', price: 250, inStock: true, whatsapp: '+905550000000' },
    { id: 2, name: 'مكتبة الفاتح', city: 'إسطنبول', price: 260, inStock: true, whatsapp: '+905550000001' },
    { id: 3, name: 'دار المعرفة', city: 'غازي عنتاب', price: 245, inStock: false, whatsapp: '+905550000002' },
    { id: 4, name: 'مكتبة النور', city: 'بورصة', price: 255, inStock: true, whatsapp: '+905550000003' },
  ];

  return (
    <div className="book-details-page container">
      <div className="book-hero glass-panel animate-fade-in">
        <div className="book-hero-cover" style={{ backgroundColor: book.coverColor }}>
          <span className="book-icon-large">📖</span>
        </div>
        <div className="book-hero-info">
          <h1 className="book-hero-title">{book.title}</h1>
          <p className="book-hero-author">المؤلف: <span>{book.author}</span></p>
          <div className="book-tags">
            <span className="tag">التصنيف: {book.category}</span>
            <span className="tag">دار النشر: {book.publisher}</span>
          </div>
          <p className="book-description">{book.description}</p>
        </div>
      </div>

      <div className="stores-section animate-fade-in animate-delay-1">
        <h2 className="section-title">المكتبات التي توفر الكتاب</h2>
        <div className="stores-table-wrapper glass-panel">
          <table className="stores-table">
            <thead>
              <tr>
                <th>اسم المكتبة</th>
                <th>المدينة</th>
                <th>السعر</th>
                <th>حالة التوفر</th>
                <th>التواصل</th>
              </tr>
            </thead>
            <tbody>
              {stores.map(store => (
                <tr key={store.id}>
                  <td className="store-name-cell">
                    <strong>{store.name}</strong>
                  </td>
                  <td>{store.city}</td>
                  <td className="price-cell">{store.price} ل.ت</td>
                  <td>
                    {store.inStock ? (
                      <span className="status-badge status-in-stock">متوفر</span>
                    ) : (
                      <span className="status-badge status-out-of-stock">نفدت الكمية</span>
                    )}
                  </td>
                  <td>
                    <a 
                      href={`https://wa.me/${store.whatsapp.replace('+', '')}`} 
                      target="_blank" 
                      rel="noreferrer" 
                      className={`btn btn-whatsapp ${!store.inStock ? 'disabled' : ''}`}
                      onClick={(e) => !store.inStock && e.preventDefault()}
                    >
                      تواصل عبر واتساب
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
