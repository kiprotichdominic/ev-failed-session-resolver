"use client";

import { useState } from "react";

export default function CopyButton({
  text,
  label = "Copy",
}: {
  text: string;
  label?: string;
}) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("failed");
    } finally {
      setTimeout(() => setState("idle"), 2000);
    }
  }

  return (
    <button
      className="border border-line-strong bg-canvas px-2 py-0.5 text-sm transition-colors hover:bg-surface focus-visible:outline-2 focus-visible:outline-offset-1 active:scale-95"
      onClick={copy}
    >
      {state === "copied"
        ? "Copied"
        : state === "failed"
          ? "Copy failed - select manually"
          : label}
    </button>
  );
}
