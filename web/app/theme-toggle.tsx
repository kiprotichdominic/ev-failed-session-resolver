"use client";

import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    setTheme(
      document.documentElement.getAttribute("data-theme") === "light"
        ? "light"
        : "dark",
    );
  }, []);

  function toggle() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    if (next === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    try {
      localStorage.setItem("theme", next);
    } catch {
      /* storage unavailable (e.g. private mode): theme just won't persist */
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      }
      className="rounded border border-line-strong px-2 py-0.5 text-sm text-muted transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-1"
    >
      {theme === "dark" ? "Light mode" : "Dark mode"}
    </button>
  );
}
