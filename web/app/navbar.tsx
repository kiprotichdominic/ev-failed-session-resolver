import Link from "next/link";
import NavLinks from "./nav-links";
import StatusDot from "./status-dot";
import ThemeToggle from "./theme-toggle";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getStatus(): Promise<{ mode: string; model: string } | null> {
  try {
    const r = await fetch(`${API}/api/status`, { cache: "no-store" });
    if (!r.ok) return null;
    return (await r.json()) as { mode: string; model: string };
  } catch {
    return null;
  }
}

export function NavbarFallback() {
  return (
    <header className="sticky top-0 z-10 border-b border-line bg-canvas">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-6 px-6 py-3">
        <Link href="/" className="text-sm font-semibold tracking-tight">
          Failed-Session Resolver
        </Link>
        <NavLinks />
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

export default async function Navbar() {
  const status = await getStatus();
  return (
    <header className="sticky top-0 z-10 border-b border-line bg-canvas">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-6 px-6 py-3">
        <Link href="/" className="text-sm font-semibold tracking-tight">
          Failed-Session Resolver
        </Link>
        <NavLinks />
        <div className="ml-auto flex items-center gap-4">
          <p className="flex items-center text-sm text-muted" role="status">
          {status === null ? (
            "API unreachable"
          ) : status.mode === "meta" ? (
            <>
              <StatusDot tone="ok" /> Live model output ({status.model})
            </>
          ) : (
            <>
              <StatusDot tone="idle" /> Canned replies, not live model output
            </>
          )}
          </p>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
