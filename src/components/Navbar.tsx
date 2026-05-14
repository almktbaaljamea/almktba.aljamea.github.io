import Link from 'next/link';
import './Navbar.css';
import ThemeToggle from './ThemeToggle';

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="container navbar-container">
        <Link href="/" className="navbar-logo" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img src="/logo.png" alt="شعار المكتبة الجامعة" style={{ height: '40px', width: 'auto' }} />
          <span className="logo-text" style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>المكتبة الجامعة</span>
        </Link>
        
        <div className="navbar-links">
          <Link href="/" className="nav-link">الرئيسية</Link>
          <Link href="/explore" className="nav-link">البحث عن كتاب</Link>
          <Link href="/bookstores" className="nav-link">دليل المكتبات</Link>
          <Link href="/about" className="nav-link">عن المنصة</Link>
        </div>
        
        <div className="navbar-actions" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <ThemeToggle />
          <Link href="/for-bookstores" className="btn btn-primary">أضف مكتبتك</Link>
        </div>
      </div>
    </nav>
  );
}
