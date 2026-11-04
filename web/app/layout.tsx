import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import Banners from "./banners";
import BottomNav from "./bottom-nav";
import "./globals.css";
import Navbar, { NavbarFallback } from "./navbar";
import Sidebar, { SidebarFallback } from "./sidebar";
import Topbar, { TopbarFallback } from "./topbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "EV-Failed-Session Resolver",
  description: "Diagnose failed EV charging sessions. All data is synthetic.",
};

export const viewport: Viewport = {
  themeColor: "#0c0c09",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="font-sans min-h-full bg-canvas text-ink">
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("theme");if(t==="light"||(t==="system"&&matchMedia("(prefers-color-scheme: light)").matches)){document.documentElement.setAttribute("data-theme","light")}}catch(e){}})();`,
          }}
        />
        <div className="flex min-h-screen">
          <Suspense fallback={<SidebarFallback />}>
            <Sidebar />
          </Suspense>
          <div className="flex min-w-0 flex-1 flex-col">
            <Suspense fallback={<NavbarFallback />}>
              <Navbar />
            </Suspense>
            <Suspense fallback={<TopbarFallback />}>
              <Topbar />
            </Suspense>
            <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 pt-6">
              <Banners />
            </div>
            {children}
            <footer className="mt-auto pt-6 pb-24 lg:pb-0">
              <div className="border-t border-line">
                <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 py-3 text-sm text-muted">
                  MIT licensed. Built for the Meta Global AI Developer
                  Hackathon 2026. An independent project, not made or endorsed
                  by Meta.
                </div>
              </div>
            </footer>
            <BottomNav />
          </div>
        </div>
      </body>
    </html>
  );
}
