import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "مكتباتنا - دليل المكتبات العربية في تركيا",
  description: "منصة رقمية تجمع المكتبات العربية في تركيا لتسهيل وصول القارئ إلى الكتب المنظمة بأسعار واضحة وتوفر مؤكد.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <Navbar />
        <main style={{ minHeight: 'calc(100vh - 200px)' }}>
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
