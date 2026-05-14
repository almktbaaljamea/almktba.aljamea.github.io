import Link from 'next/link';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-container">
        <div className="footer-section">
          <h3 className="footer-title">مكتباتنا</h3>
          <p className="footer-text">
            منصة رقمية تهدف إلى جمع المكتبات العربية في تركيا لتسهيل وصول القارئ إلى الكتب المنظمة.
          </p>
        </div>
        
        <div className="footer-section">
          <h4 className="footer-subtitle">روابط سريعة</h4>
          <ul className="footer-links">
            <li><Link href="/">الرئيسية</Link></li>
            <li><Link href="/explore">البحث عن كتاب</Link></li>
            <li><Link href="/bookstores">المكتبات المشاركة</Link></li>
            <li><Link href="/for-bookstores">أضف مكتبتك</Link></li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4 className="footer-subtitle">تواصل معنا</h4>
          <ul className="footer-links">
            <li><a href="mailto:info@arabbookstores.tr">info@arabbookstores.tr</a></li>
            <li><a href="https://instagram.com" target="_blank" rel="noreferrer">انستغرام</a></li>
            <li><a href="https://facebook.com" target="_blank" rel="noreferrer">فيسبوك</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        <p>جميع الحقوق محفوظة &copy; {new Date().getFullYear()} - منصة مكتباتنا</p>
      </div>
    </footer>
  );
}
