"use client";

import { useEffect, useState } from "react";
import { FiMonitor, FiMoon, FiSun } from "react-icons/fi";

type Choice = "dark" | "light" | "system";

const OPTIONS: { id: Choice; label: string; icon: typeof FiMoon }[] = [
  { id: "dark", label: "Dark theme", icon: FiMoon },
  { id: "light", label: "Light theme", icon: FiSun },
  { id: "system", label: "System theme", icon: FiMonitor },
];

function apply(choice: Choice): void {
  const light =
    choice === "light" ||
    (choice === "system" &&
      window.matchMedia("(prefers-color-scheme: light)").matches);
  if (light) {
    document.documentElement.setAttribute("data-theme", "light");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", light ? "#ffffff" : "#0c0c09");
}

export default function ThemeToggle() {
  const [choice, setChoice] = useState<Choice>("dark");

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    const initial: Choice =
      stored === "light" || stored === "system" ? stored : "dark";
    setChoice(initial);
    apply(initial);
  }, []);

  useEffect(() => {
    if (choice !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: light)");
    const onChange = () => apply("system");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [choice]);

  function pick(next: Choice) {
    setChoice(next);
    apply(next);
    try {
      localStorage.setItem("theme", next);
    } catch {
      /* storage unavailable: theme just won't persist */
    }
  }

  return (
    <div
      role="radiogroup"
      aria-label="Color theme"
      className="flex rounded-md border border-line-strong"
    >
      {OPTIONS.map((o) => {
        const Icon = o.icon;
        const selected = choice === o.id;
        return (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={o.label}
            title={o.label}
            onClick={() => pick(o.id)}
            className={`p-1.5 transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 ${
              selected
                ? "rounded bg-accent text-accent-ink"
                : "text-muted hover:text-ink"
            }`}
          >
            <Icon size={16} aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
}
