import Link from 'next/link';
import './page.css';
import SearchBar from '@/components/SearchBar';

export default function Home() {
  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="container hero-container">
          <div className="hero-content animate-fade-in">
            <h1 className="hero-title">البحث عن الكتب العربية في تركيا صار أسهل!</h1>
            <p className="hero-subtitle">
              منصة تجمع المكتبات العربية في مكان واحد، قارن الأسعار، وتعرف على أماكن التوفر بسرعة ووضوح.
            </p>
            <SearchBar placeholder="ابحث باسم الكتاب، المؤلف، أو دار النشر..." />
            <div className="hero-tags">
              <span>الكلمات الشائعة:</span>
              <Link href="/explore?q=روايات" className="tag">روايات</Link>
              <Link href="/explore?q=تاريخ" className="tag">تاريخ</Link>
              <Link href="/explore?q=تطوير الذات" className="tag">تطوير الذات</Link>
            </div>
          </div>
          <div className="hero-image animate-fade-in animate-delay-2">
            <div className="floating-book-card">
              <div className="book-mockup">📚</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features container">
        <h2 className="section-title text-center">ليش تستخدم مكتباتنا؟</h2>
        <div className="features-grid">
          <div className="feature-card glass-panel">
            <div className="feature-icon">🔍</div>
            <h3>بحث متقدم</h3>
            <p>لا داعي للبحث بين عشرات الصفحات، ابحث عن كتابك في جميع المكتبات بضغطة زر.</p>
          </div>
          <div className="feature-card glass-panel">
            <div className="feature-icon">💰</div>
            <h3>مقارنة الأسعار</h3>
            <p>قارن أسعار الكتب بين المكتبات المختلفة بكل شفافية لتجد أفضل سعر.</p>
          </div>
          <div className="feature-card glass-panel">
            <div className="feature-icon">📍</div>
            <h3>في مدينتك</h3>
            <p>اكتشف المكتبات العربية القريبة منك في إسطنبول، غازي عنتاب، وباقي المدن.</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container cta-container glass-panel">
          <div className="cta-content">
            <h2>هل تملك مكتبة عربية في تركيا؟</h2>
            <p>انضم إلينا الآن لتصل إلى آلاف القراء، نظم عرض كتبك، وزد من مبيعاتك.</p>
            <Link href="/for-bookstores" className="btn btn-primary btn-lg">سجل مكتبتك مجاناً</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
