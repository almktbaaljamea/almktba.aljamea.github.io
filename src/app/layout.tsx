import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { ThemeProvider } from "@/components/ThemeProvider";

export const metadata: Metadata = {
  metadataBase: new URL("https://almktba-aljamea-bot.onrender.com"),
  title: "مكتباتنا - دليل المكتبات العربية في تركيا",
  description: "منصة رقمية تجمع المكتبات العربية في تركيا لتسهيل وصول القارئ إلى الكتب المنظمة بأسعار واضحة وتوفر مؤكد.",
  openGraph: {
    title: "مكتباتنا - دليل المكتبات العربية في تركيا",
    description: "أكبر منصة رقمية للبحث عن الكتب في المكتبات العربية في تركيا.",
    url: "https://almktba-aljamea-bot.onrender.com/",
    siteName: "المكتبة الجامعة",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "المكتبة الجامعة",
      },
    ],
    locale: "ar_AR",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <ThemeProvider>
          <Navbar />
          <main style={{ minHeight: 'calc(100vh - 200px)' }}>
            {children}
          </main>
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
