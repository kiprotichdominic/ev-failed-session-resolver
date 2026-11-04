"use client";

import { usePathname } from "next/navigation";

const TITLES: Record<string, string> = {
  "/": "Cases",
  "/evaluation": "Evaluation",
  "/audit": "Audit",
};

export default function TopbarTitle() {
  const pathname = usePathname();
  return (
    <p aria-hidden="true" className="text-lg font-semibold tracking-tight">
      {TITLES[pathname] ?? "EV-Failed-Session Resolver"}
    </p>
  );
}
