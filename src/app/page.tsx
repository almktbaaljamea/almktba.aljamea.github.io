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

      {/* Contact & CTA Section */}
      <section className="cta-section container">
        <div className="cta-grid">
          <div className="cta-card glass-panel animate-fade-in">
            <h2>هل تملك مكتبة عربية في تركيا؟</h2>
            <p>انضم إلى المنصة العربية الأكبر في تركيا، وسّع انتشارك، ونظم عرض كتبك لآلاف الباحثين يومياً.</p>
            <div className="cta-benefits">
              <div className="benefit-item">✅ وصول لآلاف القراء</div>
              <div className="benefit-item">✅ نظام إدارة سهل</div>
              <div className="benefit-item">✅ مقارنة أسعار عادلة</div>
            </div>
            <a href="https://wa.me/905366768390?text=أرغب+في+تسجيل+مكتبتي+في+منصة+المكتبة+الجامعة" className="btn btn-primary btn-lg" style={{marginTop: '1.5rem'}}>
              سجل مكتبتك الآن عبر واتساب
            </a>
          </div>

          <div className="cta-card glass-panel animate-fade-in animate-delay-1">
            <h2>تواصل معنا مباشرة</h2>
            <p>لأي استفسارات أو دعم فني، نحن متاحون عبر القنوات الرسمية التالية:</p>
            <div className="contact-methods">
              <div className="contact-item">
                <span className="icon">📱</span>
                <div>
                  <strong>واتساب المنصة:</strong>
                  <a href="https://wa.me/905366768390" className="contact-link">905366768390+</a>
                </div>
              </div>
              <div className="contact-item">
                <span className="icon">📢</span>
                <div>
                  <strong>قناة التيليجرام:</strong>
                  <a href="https://t.me/almaktaba_aljamea" className="contact-link">almaktaba_aljamea@</a>
                </div>
              </div>
              <div className="contact-item">
                <span className="icon">🤖</span>
                <div>
                  <strong>بوت البحث الذكي:</strong>
                  <a href="https://t.me/almaktaba_aljameabot" className="contact-link">almaktaba_aljameabot@</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
