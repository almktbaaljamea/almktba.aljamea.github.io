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
            <h1 className="hero-title">المكتبة الجامعة</h1>
            <p className="hero-subtitle">
              المكتبة التي جَمَعَت كل المكتبات وكل الكتب في مجمع واحد. ابحث، قارن الأسعار، وتعرّف على أماكن توفر كتبك المفضلة بسرعة ووضوح.
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

      {/* Bookstore Registration Section */}
      <section className="cta-section container">
        <div className="cta-card glass-panel animate-fade-in full-width-cta">
          <h2>هل تملك مكتبة؟</h2>
          <p className="cta-intro">انضم إلى المنصة العربية للكتب والمكتبات العربية، وساعد القرّاء على الوصول إلى مكتبتك وكتبك بسهولة أكبر.</p>
          
          <div className="cta-benefits-detailed">
            <div className="benefit-item">✅ وصول لآلاف الباحثين عن الكتب العربية</div>
            <div className="benefit-item">✅ عرض منظم لكتبك وأسعارك</div>
            <div className="benefit-item">✅ زيادة ظهور مكتبتك في مختلف المدن</div>
            <div className="benefit-item">✅ تقليل الأسئلة المتكررة في الخاص</div>
            <div className="benefit-item">✅ إبراز التخفيضات والإصدارات الجديدة</div>
            <div className="benefit-item">✅ تحسين ثقة العملاء بالمكتبة</div>
          </div>
          
          <div className="cta-action-wrapper">
            <a href="https://wa.me/905366768390?text=أرغب+في+تسجيل+مكتبتي+في+منصة+المكتبة+الجامعة" className="btn btn-primary btn-lg">
              سجّل مكتبتك الآن عبر واتساب
            </a>
          </div>
        </div>
      </section>

    </div>
  );
}
