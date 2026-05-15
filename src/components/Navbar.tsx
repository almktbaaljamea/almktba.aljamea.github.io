"use client";

import Link from 'next/link';
import './Navbar.css';
import ThemeToggle from './ThemeToggle';

import { useState } from 'react';

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  return (
    <nav className="navbar">
      <div className="container navbar-container">
        <Link href="/" className="navbar-logo" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img src="/logo.png" alt="شعار المكتبة الجامعة" style={{ height: '40px', width: 'auto' }} />
          <span className="logo-text" style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>المكتبة الجامعة</span>
        </Link>
        
        <button className="mobile-menu-toggle" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          {isMenuOpen ? '✕' : '☰'}
        </button>

        <div className={`navbar-links ${isMenuOpen ? 'open' : ''}`}>
          <Link href="/" className="nav-link" onClick={() => setIsMenuOpen(false)}>الرئيسية</Link>
          <Link href="/explore" className="nav-link" onClick={() => setIsMenuOpen(false)}>البحث عن كتاب</Link>
          <Link href="/bookstores" className="nav-link" onClick={() => setIsMenuOpen(false)}>دليل المكتبات</Link>
          <Link href="/about" className="nav-link" onClick={() => setIsMenuOpen(false)}>عن المنصة</Link>
          <div className="mobile-only-actions">
            <a href="https://wa.me/905366768390?text=أرغب+في+تسجيل+مكتبتي+في+منصة+المكتبة+الجامعة" className="btn btn-primary" style={{width: '100%', textAlign: 'center'}}>أضف مكتبتك</a>
          </div>
        </div>
        
        <div className="navbar-actions">
          <ThemeToggle />
          <a href="https://wa.me/905366768390?text=أرغب+في+تسجيل+مكتبتي+في+منصة+المكتبة+الجامعة" className="btn btn-primary desktop-only">أضف مكتبتك</a>
        </div>
      </div>
    </nav>
  );
}
