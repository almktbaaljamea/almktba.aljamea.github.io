"use client";

import Link from 'next/link';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-container">
        <div className="footer-section">
          <h3 className="footer-title">المكتبة الجامعة</h3>
          <p className="footer-text">
            المكتبة التي جَمَعَت كل المكتبات وكل الكتب في مجمع واحد. وجهتك الأولى للعثور على أي كتاب من أي مكتبة.
          </p>
        </div>
        
        <div className="footer-section">
          <h4 className="footer-subtitle">روابط سريعة</h4>
          <ul className="footer-links">
            <li><Link href="/">الرئيسية</Link></li>
            <li><Link href="/explore">البحث عن كتاب</Link></li>
            <li><Link href="/bookstores">المكتبات المشاركة</Link></li>
            <li><a href="https://wa.me/905366768390?text=أرغب+في+تسجيل+مكتبتي+في+منصة+المكتبة+الجامعة" target="_blank" rel="noreferrer">أضف مكتبتك (واتساب)</a></li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4 className="footer-subtitle">تواصل معنا</h4>
          <ul className="footer-links">
            <li><a href="https://wa.me/905366768390" target="_blank" rel="noreferrer">واتساب: 905366768390+</a></li>
            <li><a href="https://t.me/your_telegram_channel" target="_blank" rel="noreferrer">قناتنا على تيليجرام 📢</a></li>
            <li><a href="https://t.me/your_book_search_bot" target="_blank" rel="noreferrer">بوت البحث عن الكتب 🤖</a></li>
            <li><a href="#" onClick={(e) => { e.preventDefault(); alert('عذراً، لم نقم بفتح حساب انستغرام للمنصة بعد. ترقبونا قريباً!'); }}>انستغرام</a></li>
            <li><a href="#" onClick={(e) => { e.preventDefault(); alert('عذراً، لم نقم بفتح حساب فيسبوك للمنصة بعد. ترقبونا قريباً!'); }}>فيسبوك</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        <p>جميع الحقوق محفوظة &copy; {new Date().getFullYear()} - المكتبة الجامعة</p>
      </div>
    </footer>
  );
}
