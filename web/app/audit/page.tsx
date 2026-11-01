"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import CopyButton from "../copy-button";
import StatusDot from "../status-dot";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Run = {
  case_id: string;
  decision: string | null;
  note: string | null;
  created_at: string;
  raw_output: string | null;
  result_json: string | null;
};

type Peek = {
  side: string | null;
  cause: string | null;
  confidence: number | null;
  verified: number;
  clauses: number;
  escalate: boolean;
  reasons: string[];
  refund: number | null;
};

function peek(resultJson: string | null): Peek | null {
  if (!resultJson) return null;
  try {
    const r = JSON.parse(resultJson);
    const verification: Record<string, boolean> = r.verification ?? {};
    const entries = Object.entries(verification);
    return {
      side: r.side ?? null,
      cause: r.cause ?? null,
      confidence: typeof r.confidence === "number" ? r.confidence : null,
      verified: entries.filter(([, ok]) => ok).length,
      clauses: entries.length,
      escalate: r.escalate === true,
      reasons: Array.isArray(r.escalate_reasons) ? r.escalate_reasons : [],
      refund: r.refund_draft ? r.refund_draft.amount_kes : null,
    };
  } catch {
    return null;
  }
}

function shortTime(iso: string): string {
  return iso.slice(0, 16).replace("T", " ");
}

const TOKEN =
  /("(?:[^"\\]|\\.)*")(:)?|\b(true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/g;

function highlightJson(src: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let k = 0;
  const punct = (from: number, to: number) => {
    if (to > from) {
      out.push(
        <span key={k++} className="text-faint">
          {src.slice(from, to)}
        </span>,
      );
    }
  };
  let m: RegExpExecArray | null;
  TOKEN.lastIndex = 0;
  while ((m = TOKEN.exec(src))) {
    punct(last, m.index);
    const [tok, str, colon, lit] = m;
    if (str !== undefined) {
      out.push(
        colon ? (
          <span key={k++} className="font-medium text-ink">
            {str}
          </span>
        ) : (
          <span key={k++} className="text-ok-ink">
            {str}
          </span>
        ),
      );
      if (colon) punct(m.index + str.length, m.index + tok.length);
    } else if (lit !== undefined) {
      out.push(
        <span key={k++} className="text-info">
          {tok}
        </span>,
      );
    } else {
      out.push(
        <span key={k++} className="text-info">
          {tok}
        </span>,
      );
    }
    last = m.index + tok.length;
  }
  punct(last, src.length);
  return out;
}

function RawOutput({ text }: { text: string }) {
  let pretty = text;
  let ok = false;
  try {
    pretty = JSON.stringify(JSON.parse(text), null, 2);
    ok = true;
  } catch {
    /* not JSON — render as plain text */
  }
  return (
    <div>
      <div className="mb-1 flex justify-start">
        <CopyButton text={text} label="Copy raw" />
      </div>
      <pre className="overflow-x-auto border border-line bg-surface p-2 font-mono text-xs">
        {ok ? highlightJson(pretty) : text}
      </pre>
    </div>
  );
}

type Filter = "all" | "undecided" | "approved" | "rejected";

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "undecided", label: "Undecided" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
];

function matches(row: Run, filter: Filter): boolean {
  if (filter === "all") return true;
  if (filter === "undecided") return row.decision === null;
  if (filter === "approved") return row.decision === "approve";
  return row.decision === "reject";
}

function DecisionBadge({ decision }: { decision: string | null }) {
  if (decision === "approve") {
    return (
      <span className="rounded-full border border-ok/30 bg-ok-tint px-2 py-0.5 text-sm">
        <StatusDot tone="ok" />
        approved
      </span>
    );
  }
  if (decision === "reject") {
    return (
      <span className="rounded-full border border-bad/30 bg-bad-tint px-2 py-0.5 text-sm">
        <StatusDot tone="bad" />
        rejected
      </span>
    );
  }
  return (
    <span className="rounded-full border border-idle/30 bg-idle-tint px-2 py-0.5 text-sm">
      <StatusDot tone="idle" />
      undecided
    </span>
  );
}

export default function AuditPage() {
  const [runs, setRuns] = useState<Run[] | null>(null);
  const [error, setError] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    fetch(`${API}/api/audit`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d) => setRuns(d.runs ?? []))
      .catch(() => {
        setRuns([]);
        setError(true);
      });
  }, []);

  const visible = (runs ?? []).filter((r) => matches(r, filter));
  const approved = (runs ?? []).filter((r) => r.decision === "approve").length;
  const rejected = (runs ?? []).filter((r) => r.decision === "reject").length;
  const undecided = (runs ?? []).filter((r) => r.decision === null).length;

  return (
    <main className="mx-auto w-full max-w-6xl px-6 pt-6">
      <h1 className="text-2xl font-bold tracking-tight">Audit</h1>
      <p className="mt-1 text-sm text-muted">
        Every resolve run, newest first, with the raw model output behind
        each row.
      </p>
      {error && (
        <p role="alert" className="mt-2 text-bad-ink">
          Could not load audit history. Restart the API to pick up the latest
          endpoints.
        </p>
      )}
      {!error && runs !== null && runs.length === 0 && (
        <p className="mt-2">
          No audit rows yet. <Link className="underline" href="/">Resolve a case</Link> first.
        </p>
      )}
      {!error && runs !== null && runs.length > 0 && (
        <>
          <p className="mt-2 text-sm tabular-nums">
            {runs.length} runs · {approved} approved · {rejected} rejected ·{" "}
            {undecided} undecided
          </p>
          <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Filter runs by decision">
            {FILTERS.map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                aria-pressed={filter === f.id}
                className={
                  filter === f.id
                    ? "border border-ink bg-ink px-2 py-0.5 text-sm text-canvas focus-visible:outline-2 focus-visible:outline-offset-1"
                    : "border border-line-strong px-2 py-0.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-1"
                }
              >
                {f.label}
              </button>
            ))}
          </div>
        </>
      )}
      <ul>
        {visible.map((row, i) => {
          const p = peek(row.result_json);
          return (
            <li
              key={`${row.case_id}-${row.created_at}-${i}`}
              className="mt-2 border-b border-line pb-2"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{row.case_id}</span>
                <DecisionBadge decision={row.decision} />
                <span className="text-sm text-muted" title={row.created_at}>
                  {shortTime(row.created_at)}
                </span>
              </div>
              {p ? (
                <div className="mt-1 text-sm">
                  <p>{p.cause ?? "—"}</p>
                  <p className="mt-0.5 text-muted">
                    {p.side ?? "no output"}
                    {p.confidence !== null &&
                      ` · ${Math.round(p.confidence * 100)}%`}
                    {p.clauses > 0 &&
                      ` · clauses ${p.verified}/${p.clauses} verified`}
                    {p.refund !== null ? ` · refund ${p.refund} KES` : ""}
                    {p.escalate
                      ? ` · escalated (${p.reasons.join(", ") || "see reasons"})`
                      : ""}
                  </p>
                </div>
              ) : (
                <p className="mt-1 text-sm text-muted">(no result recorded)</p>
              )}
              {row.note ? (
                <p className="mt-1 text-sm">Note: {row.note}</p>
              ) : null}
              <details className="mt-1">
                <summary className="cursor-pointer text-sm hover:underline">
                  Raw model output
                </summary>
                <div className="mt-1">
                  {row.raw_output === null ? (
                    <p className="text-sm text-muted">(no reply)</p>
                  ) : (
                    <RawOutput text={row.raw_output} />
                  )}
                </div>
              </details>
            </li>
          );
        })}
      </ul>
      {!error && runs !== null && runs.length > 0 && visible.length === 0 && (
        <p className="mt-2 text-sm text-muted">
          No runs match this filter.
        </p>
      )}
    </main>
  );
}
