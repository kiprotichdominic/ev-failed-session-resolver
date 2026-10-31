"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Cases" },
  { href: "/evaluation", label: "Evaluation" },
  { href: "/audit", label: "Audit" },
];

export default function NavLinks() {
  const pathname = usePathname();
  return (
    <nav className="flex gap-4 text-sm font-medium">
      {LINKS.map((l) => {
        const active =
          l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
        return (
          <Link
            key={l.href}
            href={l.href}
            aria-current={active ? "page" : undefined}
            className={
              active
                ? "text-ink underline underline-offset-4"
                : "text-muted hover:text-ink hover:underline hover:underline-offset-4"
            }
          >
            {l.label}
          </Link>
        );
      })}
    </nav>
  );
}
