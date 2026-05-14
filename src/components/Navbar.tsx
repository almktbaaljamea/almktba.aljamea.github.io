import Link from 'next/link';
import './Navbar.css';

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="container navbar-container">
        <Link href="/" className="navbar-logo">
          <span className="logo-icon">📚</span>
          <span className="logo-text">مكتباتنا</span>
        </Link>
        
        <div className="navbar-links">
          <Link href="/" className="nav-link">الرئيسية</Link>
          <Link href="/search" className="nav-link">البحث عن كتاب</Link>
          <Link href="/bookstores" className="nav-link">دليل المكتبات</Link>
          <Link href="/about" className="nav-link">عن المنصة</Link>
        </div>
        
        <div className="navbar-actions">
          <Link href="/for-bookstores" className="btn btn-primary">أضف مكتبتك</Link>
        </div>
      </div>
    </nav>
  );
}
