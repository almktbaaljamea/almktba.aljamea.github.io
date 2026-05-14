import Link from 'next/link';
import './BookCard.css';

export default function BookCard({ id, book_name, publisher, price, cover_image, library, city, onOpenModal }: any) {
  return (
    <div className="book-card glass-panel" onClick={() => onOpenModal && onOpenModal(id)}>
      <div className="book-cover">
        {cover_image ? (
          <img src={cover_image} alt={book_name} loading="lazy" style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        ) : (
          <span className="book-icon">📖</span>
        )}
      </div>
      <div className="book-info">
        <h3 className="book-title">{book_name || '---'}</h3>
        <p className="book-author">📘 {publisher || 'غير معروف'}</p>
        <p className="book-city-lib" style={{fontSize: '0.8em', color: '#94a3b8', marginBottom: '8px'}}>🏛 {library} - 📍 {city}</p>
        <div className="book-footer">
          <span className="book-price">💰 {price || 'غير متوفر'}</span>
          <span className="view-btn">عرض التفاصيل</span>
        </div>
      </div>
    </div>
  );
}
