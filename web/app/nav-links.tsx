"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Cases" },
  { href: "/evaluation", label: "Evaluation" },
  { href: "/audit", label: "Audit" },
];

export default function NavLinks({ vertical = false }: { vertical?: boolean }) {
  const pathname = usePathname();
  return (
    <nav className={vertical ? "flex flex-col gap-1" : "flex gap-4 text-sm font-medium"}>
      {LINKS.map((l) => {
        const active =
          l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
        const cls = vertical
          ? active
            ? "rounded-md border border-accent bg-accent/10 px-3 py-2 text-[15px] font-medium"
            : "rounded-md px-3 py-2 text-[15px] text-muted hover:bg-surface hover:text-ink"
          : active
            ? "text-ink underline decoration-accent decoration-2 underline-offset-4"
            : "text-muted hover:text-ink hover:underline hover:underline-offset-4";
        return (
          <Link
            key={l.href}
            href={l.href}
            aria-current={active ? "page" : undefined}
            className={cls}
          >
            {l.label}
          </Link>
        );
      })}
    </nav>
  );
}
