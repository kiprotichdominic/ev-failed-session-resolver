"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Evidence = { source: string; ref: string; note: string };
type Result = {
  case_id: string;
  side: string | null;
  cause: string | null;
  evidence: Evidence[];
  clause_ids: string[];
  confidence: number | null;
  driver_message: { language: string; text: string } | null;
  technician_note: string | null;
  calc: Record<string, number | boolean> | null;
  still_open: boolean;
  refund_draft: { amount_kes: number; requires_approval: boolean } | null;
  escalate: boolean;
  escalate_reasons: string[];
  verification: Record<string, boolean>;
};
type CaseFile = {
  case_id: string;
  complaint: { text: string };
  session_log: Record<string, string | number | null>[];
};

function citedIndexes(evidence: Evidence[]): Set<number> {
  const out = new Set<number>();
  for (const item of evidence) {
    if (item.source === "log") {
      const m = /^session_log\[(\d+)\]$/.exec(item.ref);
      if (m) out.add(Number(m[1]));
    }
  }
  return out;
}

export default function CasesPage() {
  const [cases, setCases] = useState<string[]>([]);
  const [status, setStatus] = useState<{ mode: string; model: string } | null>(null);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState<CaseFile | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [note, setNote] = useState("");
  const [decision, setDecision] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/status`)
      .then((r) => r.json())
      .then((d) => setStatus({ mode: d.mode, model: d.model }))
      .catch(() => null);
    fetch(`${API}/api/cases`)
      .then((r) => r.json())
      .then((d) => {
        const ids = d.cases.map((c: { case_id: string }) => c.case_id);
        setCases(ids);
        if (ids.length > 0) setSelected(ids[0]);
      })
      .catch(() => setError("Could not reach the API at " + API));
  }, []);

  async function resolve() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    setDecision(null);
    try {
      const [raw, res] = await Promise.all([
        fetch(`${API}/api/cases/${selected}`),
        fetch(`${API}/api/resolve/${selected}`, { method: "POST" }),
      ]);
      if (!raw.ok || !res.ok) throw new Error("resolve failed");
      setDetail(await raw.json());
      setResult(await res.json());
    } catch {
      setError("Could not resolve case. Is the API running?");
    } finally {
      setBusy(false);
    }
  }

  async function decide(choice: "approve" | "reject") {
    if (!selected) return;
    const r = await fetch(`${API}/api/cases/${selected}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision: choice, note }),
    });
    if (r.ok) {
      const row = await r.json();
      setDecision(`${row.decision} — ${row.note ?? ""}`);
    }
  }

  const cited = result ? citedIndexes(result.evidence) : new Set<number>();

  return (
    <main className="mx-auto max-w-3xl p-6">
      <p className="rounded border border-blue-300 bg-blue-50 p-2 text-sm">
        All data in this demo is synthetic.
      </p>
      {status?.mode === "meta" ? (
        <p className="mt-2 rounded border border-green-300 bg-green-50 p-2 text-sm">
          Live model output ({status.model}).
        </p>
      ) : (
        <p className="mt-2 rounded border border-amber-300 bg-amber-50 p-2 text-sm">
          Canned replies, not live model output.
        </p>
      )}

      <h1 className="mt-4 text-2xl font-bold">Cases</h1>
      {error && <p className="mt-2 text-red-700">{error}</p>}
      {cases.length === 0 && !error && (
        <p className="mt-2">No cases yet. Add case files under eval/cases/.</p>
      )}
      {cases.length > 0 && (
        <div className="mt-2 flex gap-2">
          <select
            className="border p-1"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            {cases.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
          <button
            className="border bg-gray-100 px-3 py-1 disabled:opacity-50"
            onClick={resolve}
            disabled={busy}
          >
            {busy ? "Resolving…" : "Resolve"}
          </button>
        </div>
      )}

      {detail && (
        <section className="mt-4">
          <h2 className="text-lg font-semibold">Complaint</h2>
          <p>{detail.complaint.text}</p>
          <h2 className="mt-3 text-lg font-semibold">Session log</h2>
          <table className="mt-1 w-full border-collapse text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="pr-2">#</th>
                <th className="pr-2">ts</th>
                <th className="pr-2">type</th>
                <th>detail</th>
              </tr>
            </thead>
            <tbody>
              {detail.session_log.map((entry, i) => (
                <tr
                  key={i}
                  className={cited.has(i) ? "bg-yellow-100" : undefined}
                >
                  <td className="pr-2">{i}</td>
                  <td className="pr-2">{String(entry.ts ?? "")}</td>
                  <td className="pr-2">{String(entry.type ?? "")}</td>
                  <td>
                    {["meter_wh", "status", "error_code", "reason"]
                      .filter((k) => entry[k] != null)
                      .map((k) => `${k}=${entry[k]}`)
                      .join(" ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {result && (
        <section className="mt-4">
          <h2 className="text-lg font-semibold">Result</h2>
          <p>Side: {result.side ?? "—"}</p>
          <p>Cause: {result.cause ?? "—"}</p>
          <p>Confidence: {result.confidence ?? "—"}</p>
          <p className="mt-2 font-medium">Evidence:</p>
          <ul className="list-disc pl-5">
            {result.evidence.map((item, i) => (
              <li key={i}>
                {item.source}: {item.ref} — {item.note}
              </li>
            ))}
          </ul>
          <p className="mt-2 font-medium">Clauses:</p>
          <ul className="list-disc pl-5">
            {Object.entries(result.verification).map(([id, ok]) => (
              <li key={id}>
                {id}: {ok ? "verified" : "failed"}
              </li>
            ))}
          </ul>
          <h2 className="mt-3 text-lg font-semibold">Calculation</h2>
          <p>Calc: {JSON.stringify(result.calc)}</p>
          <p>Still open: {String(result.still_open)}</p>
          <p>Technician note: {result.technician_note ?? "—"}</p>
          {result.driver_message && (
            <>
              <p>Driver message ({result.driver_message.language}):</p>
              <p>{result.driver_message.text}</p>
            </>
          )}
          {result.escalate ? (
            <div className="mt-3 rounded border border-red-300 bg-red-50 p-2">
              <p className="font-semibold">Needs human review</p>
              <ul className="list-disc pl-5">
                {result.escalate_reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
          ) : (
            result.refund_draft && (
              <div className="mt-3">
                <p>
                  Refund draft: {result.refund_draft.amount_kes} KES
                  (requires approval)
                </p>
                <input
                  className="mt-1 w-full border p-1"
                  placeholder="Decision note (optional)"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
                <div className="mt-1 flex gap-2">
                  <button
                    className="border bg-gray-100 px-3 py-1"
                    onClick={() => decide("approve")}
                  >
                    Approve
                  </button>
                  <button
                    className="border bg-gray-100 px-3 py-1"
                    onClick={() => decide("reject")}
                  >
                    Reject
                  </button>
                </div>
                {decision && <p>Recorded decision: {decision}</p>}
              </div>
            )
          )}
        </section>
      )}
    </main>
  );
}
