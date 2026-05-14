import Link from 'next/link';
import './BookCard.css';

export default function BookCard({ id, title, author, price, coverColor }: any) {
  return (
    <Link href={`/book/${id}`} className="book-card glass-panel">
      <div className="book-cover" style={{ backgroundColor: coverColor }}>
        <span className="book-icon">📖</span>
      </div>
      <div className="book-info">
        <h3 className="book-title">{title}</h3>
        <p className="book-author">{author}</p>
        <div className="book-footer">
          <span className="book-price">{price} ل.ت</span>
          <span className="view-btn">عرض التفاصيل</span>
        </div>
      </div>
    </Link>
  );
}
