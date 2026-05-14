import BookCard from '@/components/BookCard';
import SearchBar from '@/components/SearchBar';
import './search.css';

export default function SearchPage({ searchParams }: { searchParams: { q?: string } }) {
  const query = searchParams.q || '';

  // Mock Data
  const mockBooks = [
    { id: 1, title: 'البداية والنهاية', author: 'ابن كثير', price: 250, coverColor: '#8B4513' },
    { id: 2, title: 'الخيميائي', author: 'باولو كويلو', price: 120, coverColor: '#D2B48C' },
    { id: 3, title: 'مقدمة ابن خلدون', author: 'ابن خلدون', price: 300, coverColor: '#A0522D' },
    { id: 4, title: 'فن اللامبالاة', author: 'مارك مانسون', price: 150, coverColor: '#F4A460' },
    { id: 5, title: 'تاريخ الدولة العثمانية', author: 'يلماز أوزتونا', price: 400, coverColor: '#CD853F' },
    { id: 6, title: 'قواعد العشق الأربعون', author: 'إليف شافاق', price: 180, coverColor: '#DEB887' },
  ];

  return (
    <div className="search-page container">
      <div className="search-header animate-fade-in">
        <h1 className="title-main">نتائج البحث</h1>
        <p className="subtitle">
          {query ? `نتائج البحث عن: "${query}"` : 'تصفح جميع الكتب المتوفرة في المكتبات العربية'}
        </p>
        <div className="search-bar-wrapper">
          <SearchBar placeholder="ابحث عن كتاب آخر..." />
        </div>
      </div>

      <div className="search-content">
        <aside className="search-sidebar glass-panel animate-fade-in animate-delay-1">
          <h3 className="filter-title">تصفية النتائج</h3>
          
          <div className="filter-group">
            <h4 className="filter-subtitle">المدينة</h4>
            <label className="filter-label"><input type="checkbox" /> إسطنبول</label>
            <label className="filter-label"><input type="checkbox" /> غازي عنتاب</label>
            <label className="filter-label"><input type="checkbox" /> أنطاكيا</label>
            <label className="filter-label"><input type="checkbox" /> بورصة</label>
          </div>

          <div className="filter-group">
            <h4 className="filter-subtitle">التصنيف</h4>
            <label className="filter-label"><input type="checkbox" /> روايات</label>
            <label className="filter-label"><input type="checkbox" /> تاريخ</label>
            <label className="filter-label"><input type="checkbox" /> تطوير الذات</label>
            <label className="filter-label"><input type="checkbox" /> ديني</label>
          </div>
        </aside>

        <div className="search-results">
          <div className="books-grid">
            {mockBooks.map((book, index) => (
              <div key={book.id} className={`animate-fade-in animate-delay-${(index % 3) + 1}`}>
                <BookCard {...book} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
