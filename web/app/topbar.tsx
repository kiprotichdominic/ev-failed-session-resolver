import StatusDot from "./status-dot";
import ThemeToggle from "./theme-toggle";
import TopbarTitle from "./topbar-title";

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

export function TopbarFallback() {
  return (
    <div className="sticky top-0 z-10 hidden h-14 items-center justify-between border-b border-line bg-canvas px-6 lg:flex">
      <TopbarTitle />
    </div>
  );
}

export default async function Topbar() {
  const status = await getStatus();
  return (
    <div className="sticky top-0 z-10 hidden h-14 items-center justify-between border-b border-line bg-canvas/90 px-6 backdrop-blur lg:flex">
      <TopbarTitle />
      <div className="flex items-center gap-4">
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
  );
}
