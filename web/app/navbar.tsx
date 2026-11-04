import Link from "next/link";
import Logo from "./logo";
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
    <header className="sticky top-0 z-10 border-b border-line bg-canvas lg:hidden">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm font-semibold tracking-tight hover:text-accent focus-visible:outline-2 focus-visible:outline-offset-4"
        >
          <Logo size={20} />
          EV-Failed-Session Resolver
        </Link>
        <div className="ml-auto hidden sm:block">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

export default async function Navbar() {
  const status = await getStatus();
  return (
    <header className="sticky top-0 z-10 border-b border-line bg-canvas lg:hidden">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm font-semibold tracking-tight hover:text-accent focus-visible:outline-2 focus-visible:outline-offset-4"
        >
          <Logo size={20} />
          EV-Failed-Session Resolver
        </Link>
        <div className="ml-auto hidden items-center gap-4 sm:flex">
          <ThemeToggle />
        </div>
        <div className="flex basis-full items-center gap-4 lg:basis-auto">
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
        </div>
      </div>
    </header>
  );
}
