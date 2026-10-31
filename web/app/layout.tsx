import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import Banners from "./banners";
import "./globals.css";
import Navbar, { NavbarFallback } from "./navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Failed-Session Resolver",
  description: "Diagnose failed EV charging sessions. All data is synthetic.",
};

export const viewport: Viewport = {
  themeColor: "#0c0c09",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="font-sans min-h-full flex flex-col bg-canvas text-ink">
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{if(localStorage.getItem("theme")==="light"){document.documentElement.setAttribute("data-theme","light")}}catch(e){}})();`,
          }}
        />
        <Suspense fallback={<NavbarFallback />}>
          <Navbar />
        </Suspense>
        <div className="mx-auto w-full max-w-6xl px-6 pt-6">
          <Banners />
        </div>
        {children}
      </body>
    </html>
  );
}
