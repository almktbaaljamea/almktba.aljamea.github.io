"use client";
import Link from 'next/link';
import './BookCard.css';
import { useState, useEffect } from 'react';

const imageCache: Record<string, string> = {};

export default function BookCard(props: any) {
  const { id, book_name, publisher, price, cover_image, library, city, isbn, onOpenModal } = props;
  const [imageSrc, setImageSrc] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    if (book_name) {
      if (imageCache[book_name]) {
        setImageSrc(imageCache[book_name]);
        return;
      }
      
      const fetchImage = async () => {
        try {
          const res = await fetch(`https://www.googleapis.com/books/v1/volumes?q=intitle:${encodeURIComponent(book_name)}&maxResults=1`);
          const data = await res.json();
          if (data.items && data.items.length > 0) {
            const img = data.items[0].volumeInfo?.imageLinks?.thumbnail;
            if (img && isMounted) {
               const secureImg = img.replace('http:', 'https:');
               imageCache[book_name] = secureImg;
               setImageSrc(secureImg);
            }
          }
        } catch (e) {
          console.error("Error fetching book cover", e);
        }
      };
      
      const timer = setTimeout(fetchImage, 200 + Math.random() * 500); // jitter to avoid rate limits
      return () => {
        isMounted = false;
        clearTimeout(timer);
      };
    }
  }, [book_name]);

  const displayImage = imageSrc || cover_image;

  const handleOpenModal = () => {
    if (onOpenModal) {
      // Pass the updated book object so the modal gets the accurate image
      onOpenModal({ ...props, cover_image: displayImage });
    }
  };

  return (
    <div className="book-card glass-panel" onClick={handleOpenModal}>
      <div className="book-cover">
        {displayImage ? (
          <img src={displayImage} alt={book_name} loading="lazy" style={{width: '100%', height: '100%', objectFit: 'cover'}} />
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
