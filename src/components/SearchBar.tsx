'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import './SearchBar.css';

export default function SearchBar({ placeholder = "ابحث..." }: { placeholder?: string }) {
  const [query, setQuery] = useState('');
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/explore?q=${encodeURIComponent(query)}`);
    }
  };

  return (
    <form className="search-bar" onSubmit={handleSearch}>
      <input
        type="text"
        className="search-input"
        placeholder={placeholder}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button type="submit" className="search-btn btn-primary">
        بحث
      </button>
    </form>
  );
}
