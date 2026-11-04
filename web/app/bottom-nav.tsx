"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FiBarChart2, FiClock, FiFolder } from "react-icons/fi";

const LINKS = [
  { href: "/", label: "Cases", icon: FiFolder },
  { href: "/evaluation", label: "Evaluation", icon: FiBarChart2 },
  { href: "/audit", label: "Audit", icon: FiClock },
];

export default function BottomNav() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-3 border-t border-line bg-canvas/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden"
    >
      {LINKS.map((l) => {
        const active =
          l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
        const Icon = l.icon;
        return (
          <Link
            key={l.href}
            href={l.href}
            aria-current={active ? "page" : undefined}
            className={`relative flex min-h-[56px] flex-col items-center justify-center gap-1 py-2 text-xs font-medium ${
              active ? "text-accent" : "text-muted hover:text-ink"
            }`}
          >
            {active && (
              <span
                aria-hidden="true"
                className="absolute inset-x-8 top-0 h-0.5 rounded-full bg-accent"
              />
            )}
            <Icon size={20} aria-hidden="true" />
            {l.label}
          </Link>
        );
      })}
    </nav>
  );
}
