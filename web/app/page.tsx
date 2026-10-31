"use client";

import { useEffect, useState } from "react";
import CopyButton from "./copy-button";
import StatusDot from "./status-dot";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SAMPLE_CASE = `{
  "case_id": "C-014",
  "complaint": {"text": "nimelipa 1000 lakini hakuna power", "received_at": "2026-10-21T18:42:00+03:00"},
  "session_log": [
    {"ts": "2026-10-21T18:31:02+03:00", "type": "StartTransaction", "connector_id": 1, "meter_wh": 0},
    {"ts": "2026-10-21T18:33:10+03:00", "type": "StatusNotification", "connector_id": 1, "status": "Faulted", "error_code": "GroundFailure"},
    {"ts": "2026-10-21T18:33:41+03:00", "type": "StopTransaction", "connector_id": 1, "meter_wh": 1200, "reason": "EmergencyStop"}
  ],
  "payment": {"method": "mobile_money", "currency": "KES", "held": 1000, "captured": 1000, "status": "captured"},
  "tariff_kes_per_kwh": 25
}`;

const SAMPLE_C021 = `{
  "case_id": "C-021",
  "complaint": {"text": "I paid 500 bob but the charger never started, still shows available", "received_at": "2026-10-22T09:15:00+03:00"},
  "session_log": [
    {"ts": "2026-10-22T09:02:00+03:00", "type": "StatusNotification", "connector_id": 2, "status": "Available"},
    {"ts": "2026-10-22T09:07:00+03:00", "type": "Heartbeat"},
    {"ts": "2026-10-22T09:12:00+03:00", "type": "Heartbeat"}
  ],
  "payment": {"method": "mobile_money", "currency": "KES", "held": 500, "captured": 0, "status": "pending"},
  "tariff_kes_per_kwh": 25
}`;

const SAMPLE_C032 = `{
  "case_id": "C-032",
  "complaint": {"text": "niliweka 1000 kwa charge lakini ilikataa katikati, screen ikaonyesha error", "received_at": "2026-10-23T14:20:00+03:00"},
  "session_log": [
    {"ts": "2026-10-23T14:05:00+03:00", "type": "StartTransaction", "connector_id": 1, "meter_wh": 0},
    {"ts": "2026-10-23T14:18:30+03:00", "type": "StatusNotification", "connector_id": 1, "status": "Faulted", "error_code": "GroundFailure"},
    {"ts": "2026-10-23T14:19:02+03:00", "type": "StopTransaction", "connector_id": 1, "meter_wh": 8500, "reason": "EmergencyStop"}
  ],
  "payment": {"method": "mobile_money", "currency": "KES", "held": 1000, "captured": 1000, "status": "captured"},
  "tariff_kes_per_kwh": 25
}`;

const SAMPLE_LABELS: Record<string, string> = {
  "C-014":
    '"C-014": {"split": "dev", "side": "charger", "clause_ids": ["OCPP16-ERR-GroundFailure"], "escalate": false, "refund_kes": 970}',
  "C-021":
    '"C-021": {"split": "dev", "side": "payment", "clause_ids": [], "escalate": true, "refund_kes": null}',
  "C-032":
    '"C-032": {"split": "dev", "side": "charger", "clause_ids": ["OCPP16-ERR-GroundFailure"], "escalate": false, "refund_kes": 787}',
};

const SAMPLE_CASES: Record<string, { json: string; label: string }> = {
  "C-014": { json: SAMPLE_CASE, label: SAMPLE_LABELS["C-014"] },
  "C-021": { json: SAMPLE_C021, label: SAMPLE_LABELS["C-021"] },
  "C-032": { json: SAMPLE_C032, label: SAMPLE_LABELS["C-032"] },
};

const FAULT_SIDE: Record<string, string> = {
  GroundFailure: "charger",
  OverCurrentFailure: "charger",
  HighTemperature: "charger",
  ConnectorLockFailure: "charger",
  EVCommunicationError: "vehicle",
};

type GenLang = "en" | "sw" | "sheng" | "fr" | "de" | "it" | "zh" | "pt";

const GEN_LANGS: { code: GenLang; label: string }[] = [
  { code: "en", label: "English" },
  { code: "sw", label: "Swahili" },
  { code: "sheng", label: "Sheng" },
  { code: "fr", label: "French" },
  { code: "de", label: "German" },
  { code: "it", label: "Italian" },
  { code: "zh", label: "Chinese" },
  { code: "pt", label: "Portuguese" },
];

const GEN_COMPLAINTS: Record<"fault" | "never", Record<GenLang, string>> = {
  fault: {
    en: "The charging session stopped with an error before my car was full.",
    sw: "Chaji ilisimama na hitilafu kabla gari haijajaa.",
    sheng: "Chaji ilistop na error kabla gari ijaze.",
    fr: "La session de charge s'est arrêtée sur une erreur avant que ma voiture soit chargée.",
    de: "Der Ladevorgang wurde mit einem Fehler abgebrochen, bevor mein Auto vollständig geladen war.",
    it: "La sessione di ricarica si è interrotta con un errore prima che la mia auto fosse carica.",
    pt: "A sessão de carregamento parou com um erro antes de o meu carro estar carregado.",
    zh: "我的车还没充满，充电就出错停止了。",
  },
  never: {
    en: "I paid but the charger never started.",
    sw: "Nimelipa lakini chaja haijaanza.",
    sheng: "Nimelipa lakini chaja haija-start.",
    fr: "J'ai payé mais le chargeur n'a jamais démarré.",
    de: "Ich habe bezahlt, aber das Ladegerät ist nie gestartet.",
    it: "Ho pagato ma il caricatore non è mai partito.",
    pt: "Paguei mas o carregador nunca arrancou.",
    zh: "我付了钱，但充电桩一直没启动。",
  },
};

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

function parseLogRef(ref: string): number | null {
  const m = /^session_log\[(\d+)\]$/.exec(ref);
  return m ? Number(m[1]) : null;
}

function citedIndexes(evidence: Evidence[], logLength: number): Set<number> {
  const out = new Set<number>();
  for (const item of evidence) {
    if (item.source === "log") {
      const i = parseLogRef(item.ref);
      if (i !== null && i < logLength) out.add(i);
    }
  }
  return out;
}

function reducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function scrollToId(id: string, block: ScrollLogicalPosition = "start") {
  document
    .getElementById(id)
    ?.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block });
}

function LogEvidenceRef({ itemRef, logLength }: { itemRef: string; logLength: number }) {
  const i = parseLogRef(itemRef);
  if (i === null || i >= logLength) {
    return (
      <span>
        {itemRef}{" "}
        <span className="text-xs font-medium text-bad-ink">
          [bad ref]
        </span>
      </span>
    );
  }
  return (
    <button
      className="underline focus-visible:outline-2 focus-visible:outline-offset-1"
      onClick={() => scrollToId(`log-${i}`, "center")}
      title={`Scroll to log row ${i}`}
    >
      {itemRef}
    </button>
  );
}

function LogTable({
  entries,
  indexes,
  cited,
}: {
  entries: CaseFile["session_log"];
  indexes: number[];
  cited: Set<number>;
}) {
  return (
    <table className="mt-1 w-full border-collapse font-mono text-sm tabular-nums">
      <thead>
        <tr className="border-b border-line text-left">
          <th className="pr-2">#</th>
          <th className="pr-2">ts</th>
          <th className="pr-2">type</th>
          <th>detail</th>
        </tr>
      </thead>
      <tbody>
        {indexes.map((i) => {
          const entry = entries[i];
          const isCited = cited.has(i);
          return (
            <tr
              key={i}
              id={`log-${i}`}
              className={
                isCited ? "bg-mark" : "hover:bg-surface"
              }
            >
              <td className="whitespace-nowrap pr-2">
                {i}
                {isCited && (
                  <>
                    <span aria-hidden="true"> ●</span>
                    <span className="sr-only"> (cited as evidence)</span>
                  </>
                )}
              </td>
              <td className="pr-2" title={String(entry.ts ?? "")}>
                {String(entry.ts ?? "").slice(0, 16).replace("T", " ")}
              </td>
              <td className="pr-2">{String(entry.type ?? "")}</td>
              <td>
                {["meter_wh", "status", "error_code", "reason"]
                  .filter((k) => entry[k] != null)
                  .map((k) => `${k}=${entry[k]}`)
                  .join(" ")}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

const field =
  "border border-line-strong bg-canvas p-1 transition-colors hover:bg-surface focus-visible:outline-2 focus-visible:outline-offset-1 active:scale-95";
const primary =
  "border border-ink bg-ink px-3 py-1 text-canvas transition-colors hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-1 active:scale-95 disabled:opacity-50";
const muted = "text-muted";

const STAGES = [
  "Reading complaint and session log",
  "Computing energy, owed and refund",
  "Consulting the model",
  "Verifying citations and escalation rules",
];

export default function CasesPage() {
  const [cases, setCases] = useState<string[]>([]);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState<CaseFile | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [note, setNote] = useState("");
  const [decision, setDecision] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [showBusy, setShowBusy] = useState(false);
  const [sample, setSample] = useState("C-014");
  const [pasted, setPasted] = useState("");
  const [analyserOpen, setAnalyserOpen] = useState(false);
  const [genScenario, setGenScenario] = useState<"fault" | "never">("fault");
  const [genFault, setGenFault] = useState("GroundFailure");
  const [genEnergy, setGenEnergy] = useState(4);
  const [genPaid, setGenPaid] = useState(1000);
  const [genStatus, setGenStatus] = useState<"captured" | "pending">("captured");
  const [genCaseId, setGenCaseId] = useState("C-101");
  const [genLang, setGenLang] = useState<GenLang>("en");
  const [genComplaint, setGenComplaint] = useState(GEN_COMPLAINTS.fault.en);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/api/cases`)
      .then((r) => r.json())
      .then((d) => {
        const ids = d.cases.map((c: { case_id: string }) => c.case_id);
        setCases(ids);
        if (ids.length > 0) setSelected(ids[0]);
      })
      .catch(() => setError("Could not reach the API at " + API));
  }, []);

  useEffect(() => {
    if (!busy) {
      setShowBusy(false);
      return;
    }
    setElapsed(0);
    setShowBusy(false);
    const show = setTimeout(() => setShowBusy(true), 500);
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => {
      clearTimeout(show);
      clearInterval(t);
    };
  }, [busy]);

  function selectCase(id: string) {
    setSelected(id);
    setDetail(null);
    setResult(null);
    setDecision(null);
    setConfirming(false);
    setNote("");
    setError(null);
  }

  async function resolve() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    setDecision(null);
    setConfirming(false);
    try {
      const [raw, res] = await Promise.all([
        fetch(`${API}/api/cases/${selected}`),
        fetch(`${API}/api/resolve/${selected}`, { method: "POST" }),
      ]);
      if (!raw.ok || !res.ok) throw new Error("resolve failed");
      setDetail(await raw.json());
      setResult(await res.json());
      requestAnimationFrame(() => scrollToId("diagnosis"));
    } catch {
      setError("Could not resolve case. Is the API running?");
    } finally {
      setBusy(false);
    }
  }

  async function generateComplaint() {
    setGenerating(true);
    setGenError(null);
    try {
      const r = await fetch(`${API}/api/generate-complaint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario: genScenario,
          fault_code: genScenario === "fault" ? genFault : null,
          language: genLang,
          paid_kes: genPaid,
        }),
      });
      if (!r.ok) throw new Error("generate failed");
      const d = await r.json();
      if (typeof d.text !== "string" || d.text.trim() === "") {
        throw new Error("empty reply");
      }
      setGenComplaint(d.text.trim().slice(0, 500));
    } catch {
      setGenError("Could not generate a complaint. Is the API running?");
    } finally {
      setGenerating(false);
    }
  }

  async function analysePasted() {
    let parsed: unknown;
    try {
      parsed = JSON.parse(pasted);
    } catch {
      setError("Pasted text is not valid JSON.");
      return;
    }
    const p = parsed as Partial<CaseFile> & { case_id?: unknown };
    if (
      typeof p !== "object" ||
      p === null ||
      typeof p.complaint?.text !== "string" ||
      !Array.isArray(p.session_log)
    ) {
      setError("JSON is not a case: need complaint.text and session_log.");
      return;
    }
    setBusy(true);
    setError(null);
    setDecision(null);
    setConfirming(false);
    try {
      const r = await fetch(`${API}/api/analyse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      });
      if (r.status === 422) {
        setError(
          "The API rejected this JSON as a case: check required fields and types.",
        );
        return;
      }
      if (!r.ok) throw new Error("analyse failed");
      setDetail({
        case_id: typeof p.case_id === "string" ? p.case_id : "pasted-case",
        complaint: { text: p.complaint.text },
        session_log: p.session_log as CaseFile["session_log"],
      });
      setResult(await r.json());
      requestAnimationFrame(() => scrollToId("diagnosis"));
    } catch {
      setError("Could not analyse pasted case. Is the API running?");
    } finally {
      setBusy(false);
    }
  }

  async function decide(choice: "approve" | "reject") {
    const id = result?.case_id;
    if (!id) return;
    setDeciding(true);
    try {
      const r = await fetch(`${API}/api/cases/${id}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision: choice, note }),
      });
      if (!r.ok) throw new Error("decision failed");
      const row = await r.json();
      setDecision(`${row.decision} — ${row.note ?? ""}`);
      setConfirming(false);
    } catch {
      setError("Could not record decision. Is the API running?");
    } finally {
      setDeciding(false);
    }
  }

  const genId = genCaseId.trim() === "" ? "C-XXX" : genCaseId.trim();
  const genOwed = genScenario === "fault" ? genEnergy * 25 : 0;
  const genCaptured = genStatus === "captured" ? genPaid : 0;
  const genNoSession = genScenario === "never";
  const genPendingPay = genStatus !== "captured";
  const genUnderpaid =
    !genNoSession && !genPendingPay && genCaptured < genOwed;
  const genEscalate = genNoSession || genPendingPay || genUnderpaid;
  const genEscalateWhy = [
    genNoSession ? "no session" : null,
    genPendingPay ? "payment pending" : null,
    genUnderpaid ? "underpaid" : null,
  ].filter((x): x is string => x !== null);
  const genRefundRaw = genEscalate ? null : genCaptured - genOwed;
  const genRefund = genRefundRaw === 0 ? null : genRefundRaw;
  const genSide = genNoSession ? "payment" : FAULT_SIDE[genFault];
  const genClauses = genNoSession ? [] : [`OCPP16-ERR-${genFault}`];
  const genLog =
    genScenario === "fault"
      ? [
          {
            ts: "2026-10-24T10:00:00+03:00",
            type: "StartTransaction",
            connector_id: 1,
            meter_wh: 0,
          },
          {
            ts: "2026-10-24T10:12:00+03:00",
            type: "StatusNotification",
            connector_id: 1,
            status: "Faulted",
            error_code: genFault,
          },
          {
            ts: "2026-10-24T10:13:00+03:00",
            type: "StopTransaction",
            connector_id: 1,
            meter_wh: genEnergy * 1000,
            reason: "EmergencyStop",
          },
        ]
      : [
          {
            ts: "2026-10-24T09:02:00+03:00",
            type: "StatusNotification",
            connector_id: 1,
            status: "Available",
          },
          { ts: "2026-10-24T09:07:00+03:00", type: "Heartbeat" },
          { ts: "2026-10-24T09:12:00+03:00", type: "Heartbeat" },
        ];
  const genCaseJson = JSON.stringify(
    {
      case_id: genId,
      complaint: {
        text: genComplaint,
        received_at: "2026-10-24T10:20:00+03:00",
      },
      session_log: genLog,
      payment: {
        method: "mobile_money",
        currency: "KES",
        held: genPaid,
        captured: genCaptured,
        status: genStatus,
      },
      tariff_kes_per_kwh: 25,
    },
    null,
    2,
  );
  const genLabelRow = `"${genId}": ${JSON.stringify({
    split: "dev",
    side: genSide,
    clause_ids: genClauses,
    escalate: genEscalate,
    refund_kes: genRefund,
  })}`;

  const logLength = detail?.session_log.length ?? 0;
  const cited = result ? citedIndexes(result.evidence, logLength) : new Set<number>();
  const confidence = result?.confidence ?? 0;
  const citedIdx = [...Array(logLength).keys()].filter((i) => cited.has(i));
  const otherIdx = [...Array(logLength).keys()].filter((i) => !cited.has(i));

  function reasonDetail(reason: string): string | null {
    if (reason === "low confidence" && result?.confidence !== null) {
      return `(${Math.round(confidence * 100)}% — see Diagnosis)`;
    }
    if (reason === "unverified citation") {
      return "(see failed clause above)";
    }
    return null;
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-6 pt-6">
      <h1 className="text-2xl font-bold tracking-tight">Cases</h1>
      <p className={`mt-1 text-sm ${muted}`}>
        Pick a case and resolve it: the model explains, code computes every
        number, and a human approves any refund.
      </p>
      <p className={`mt-1 text-sm ${muted}`}>
        Pick a case below, press Resolve, then review the diagnosis and record
        a decision.
      </p>
      {error && (
        <p role="alert" className="mt-2 text-bad-ink">
          {error}
        </p>
      )}
      {cases.length === 0 && !error && (
        <p className="mt-3">
          No cases yet. Open Sample cases below, copy one, save it under
          eval/cases/, and refresh this page.
        </p>
      )}
      {cases.length > 0 && (
        <div className="mt-3 flex items-center gap-2">
          <label htmlFor="case-select" className="text-sm font-medium">
            Case
          </label>
          <select
            id="case-select"
            className={field}
            value={selected}
            disabled={busy}
            onChange={(e) => selectCase(e.target.value)}
          >
            {cases.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
          <button
            className={primary}
            onClick={resolve}
            disabled={busy}
          >
            {busy ? "Resolving…" : "Resolve"}
          </button>
        </div>
      )}
      <details
        id="analyser"
        className="mt-3"
        open={analyserOpen}
        onToggle={(e) => setAnalyserOpen(e.currentTarget.open)}
      >
        <summary className="cursor-pointer text-sm hover:underline">
          Analyse pasted JSON (no file needed)
        </summary>
        <label
          htmlFor="paste-case"
          className="mt-2 block text-sm font-medium"
        >
          Case JSON
        </label>
        <textarea
          id="paste-case"
          className="mt-1 w-full border border-line-strong bg-canvas p-1 font-mono text-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-1"
          rows={8}
          value={pasted}
          onChange={(e) => setPasted(e.target.value)}
          placeholder="Paste case JSON here: same shape as eval/cases/C-014.json."
          spellCheck={false}
        />
        <div className="mt-2">
          <button
            className={primary}
            onClick={analysePasted}
            disabled={busy || pasted.trim() === ""}
          >
            {busy ? "Analysing…" : "Analyse"}
          </button>
        </div>
      </details>
      <details className="mt-3">
        <summary className="cursor-pointer text-sm hover:underline">
          Sample cases: generate file-ready text to save by hand
        </summary>
        <div className="mt-2 flex gap-2">
          {["C-014", "C-021", "C-032"].map((id) => (
            <button
              key={id}
              onClick={() => setSample(id)}
              aria-pressed={sample === id}
              className={sample === id ? primary : `${field} px-3`}
            >
              {id}
            </button>
          ))}
        </div>
        <div className="mt-2">
          <button
            className={`${field} px-3`}
            onClick={() => {
              setPasted(SAMPLE_CASES[sample].json);
              setAnalyserOpen(true);
              scrollToId("analyser");
            }}
          >
            Use {sample} in analyser
          </button>
        </div>
        <p className="mt-2 text-sm">
          Save as <code className="font-mono">eval/cases/{sample}.json</code>,
          add its label row to{" "}
          <code className="font-mono">eval/labels.json</code>, then refresh.
        </p>
        <div className="mt-2">
          <CopyButton
            text={SAMPLE_CASES[sample].json}
            label="Copy case JSON"
          />
        </div>
        <pre className="mt-2 overflow-x-auto border border-line bg-surface p-2 font-mono text-xs">
          {SAMPLE_CASES[sample].json}
        </pre>
        <div className="mt-2">
          <CopyButton
            text={SAMPLE_CASES[sample].label}
            label="Copy label row"
          />
        </div>
        <pre className="mt-2 overflow-x-auto border border-line bg-surface p-2 font-mono text-xs">
          {SAMPLE_CASES[sample].label}
        </pre>
      </details>
      <details className="mt-3">
        <summary className="cursor-pointer text-sm hover:underline">
          Build a custom sample (generate case + label draft)
        </summary>
        <div className="mt-2 grid max-w-2xl gap-3 md:grid-cols-2">
          <div>
            <label
              htmlFor="gen-scenario"
              className="block text-sm font-medium"
            >
              Scenario
            </label>
            <select
              id="gen-scenario"
              className={`${field} mt-1 w-full`}
              value={genScenario}
              onChange={(e) => {
                const v = e.target.value as "fault" | "never";
                setGenScenario(v);
                setGenComplaint(GEN_COMPLAINTS[v][genLang]);
              }}
            >
              <option value="fault">Failed session (fault)</option>
              <option value="never">Never started (no session)</option>
            </select>
          </div>
          <div>
            <label htmlFor="gen-fault" className="block text-sm font-medium">
              Fault code
            </label>
            <select
              id="gen-fault"
              className={`${field} mt-1 w-full disabled:opacity-50`}
              value={genFault}
              onChange={(e) => setGenFault(e.target.value)}
              disabled={genScenario === "never"}
            >
              {Object.keys(FAULT_SIDE).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="gen-energy" className="block text-sm font-medium">
              Energy delivered: {genEnergy} kWh → {genOwed} KES owed
            </label>
            <input
              id="gen-energy"
              type="range"
              min={0}
              max={10}
              step={1}
              value={genEnergy}
              onChange={(e) => setGenEnergy(Number(e.target.value))}
              disabled={genScenario === "never"}
              className="mt-2 w-full accent-ink disabled:opacity-50"
            />
          </div>
          <div>
            <label htmlFor="gen-paid" className="block text-sm font-medium">
              Paid (KES)
            </label>
            <input
              id="gen-paid"
              type="number"
              min={0}
              step={50}
              value={genPaid}
              onChange={(e) =>
                setGenPaid(Math.max(0, Math.floor(Number(e.target.value) || 0)))
              }
              className={`${field} mt-1 w-full`}
            />
          </div>
          <div>
            <label htmlFor="gen-status" className="block text-sm font-medium">
              Payment status
            </label>
            <select
              id="gen-status"
              className={`${field} mt-1 w-full`}
              value={genStatus}
              onChange={(e) =>
                setGenStatus(e.target.value as "captured" | "pending")
              }
            >
              <option value="captured">captured</option>
              <option value="pending">pending</option>
            </select>
          </div>
          <div>
            <label htmlFor="gen-id" className="block text-sm font-medium">
              Case ID
            </label>
            <input
              id="gen-id"
              value={genCaseId}
              onChange={(e) => setGenCaseId(e.target.value)}
              className={`${field} mt-1 w-full`}
            />
          </div>
          <div>
            <label htmlFor="gen-lang" className="block text-sm font-medium">
              Complaint language
            </label>
            <select
              id="gen-lang"
              className={`${field} mt-1 w-full`}
              value={genLang}
              onChange={(e) => {
                const v = e.target.value as GenLang;
                setGenLang(v);
                setGenComplaint(GEN_COMPLAINTS[genScenario][v]);
              }}
            >
              {GEN_LANGS.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-3 flex max-w-2xl flex-wrap items-center gap-2">
          <label htmlFor="gen-complaint" className="text-sm font-medium">
            Complaint (sets reply language)
          </label>
          <button
            className={`${field} px-3`}
            onClick={generateComplaint}
            disabled={generating}
          >
            {generating ? "Generating…" : "Generate with AI"}
          </button>
        </div>
        {genError && (
          <p role="alert" className="mt-1 text-sm text-bad-ink">
            {genError}
          </p>
        )}
        <textarea
          id="gen-complaint"
          rows={2}
          value={genComplaint}
          onChange={(e) => setGenComplaint(e.target.value)}
          className="mt-1 w-full max-w-2xl border border-line-strong bg-canvas p-1 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-1"
        />
        <p className={`mt-2 text-sm ${muted}`}>
          {genEscalate
            ? `Draft label expects escalation (${genEscalateWhy.join(", ")}).`
            : "Draft label expects no escalation."}{" "}
          Tariff fixed at 25 KES/kWh so every figure is exact. Verify after
          resolving: the live model can always force escalation.
        </p>
        {genScenario === "fault" && genFault !== "GroundFailure" && (
          <p className="mt-1 text-sm text-idle-ink">
            Only GroundFailure has a corpus entry today; expect escalation
            until the {genFault} summary is added.
          </p>
        )}
        <p className="mt-1 text-sm">
          Save as <code className="font-mono">eval/cases/{genId}.json</code>,
          add its label row to{" "}
          <code className="font-mono">eval/labels.json</code>, then refresh.
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <CopyButton text={genCaseJson} label="Copy case JSON" />
          <CopyButton text={genLabelRow} label="Copy label row" />
          <button
            className={`${field} px-3`}
            onClick={() => {
              setPasted(genCaseJson);
              setAnalyserOpen(true);
              scrollToId("analyser");
            }}
          >
            Use in analyser
          </button>
        </div>
        <pre className="mt-2 overflow-x-auto border border-line bg-surface p-2 font-mono text-xs">
          {genCaseJson}
        </pre>
        <pre className="mt-2 overflow-x-auto border border-line bg-surface p-2 font-mono text-xs">
          {genLabelRow}
        </pre>
      </details>
      {busy && showBusy && (
        <p className="mt-3 flex items-center gap-2 text-sm" role="status">
          <span
            aria-hidden="true"
            className={`inline-block h-2 w-2 rounded-full bg-ink ${reducedMotion() ? "" : "animate-pulse"}`}
          />
          {STAGES[Math.floor(elapsed / 2) % STAGES.length]}…
          <span aria-hidden="true" className={`tabular-nums ${muted}`}>
            {elapsed}s
          </span>
        </p>
      )}

      {result && (
        <div className="mt-3 flex flex-wrap items-center gap-2 rounded border border-line p-2 text-sm">
          <span className="rounded-full border border-line-strong px-2 py-0.5 font-medium">
            {result.side ?? "no model output"}
          </span>
          {result.confidence !== null && (
            <span className={`${muted} tabular-nums`}>
              {Math.round(confidence * 100)}%
            </span>
          )}
          {result.escalate ? (
            <span className="rounded-full border border-bad/30 bg-bad-tint px-2 py-0.5 font-medium">
              <StatusDot tone="bad" />
              Needs human review
            </span>
          ) : (
            <span className="rounded-full border border-ok/30 bg-ok-tint px-2 py-0.5 font-medium">
              <StatusDot tone="ok" />
              No escalation
            </span>
          )}
          {result.refund_draft && (
            <span className="tabular-nums">
              Refund draft: {result.refund_draft.amount_kes} KES
            </span>
          )}
        </div>
      )}

      {(detail || result) && (
        <div className="mt-6 grid items-start gap-6 lg:grid-cols-2">
          <div>
      {detail && (
        <section>
          <h2 className="text-lg font-semibold">Complaint</h2>
          <div className="mt-1 rounded border border-line bg-surface p-3">
            <p>{detail.complaint.text}</p>
          </div>
          <h2 className="mt-4 text-lg font-semibold">Session log</h2>
          <p className={`text-sm ${muted}`}>
            Highlighted rows are cited as evidence. Click an evidence ref below
            to jump to its row.
          </p>
          {cited.size === 0 || otherIdx.length === 0 ? (
            <LogTable
              entries={detail.session_log}
              indexes={[...Array(logLength).keys()]}
              cited={cited}
            />
          ) : (
            <>
              <LogTable
                entries={detail.session_log}
                indexes={citedIdx}
                cited={cited}
              />
              <details className="mt-2">
                <summary className="cursor-pointer text-sm hover:underline">
                  Show all {logLength} rows ({cited.size} cited)
                </summary>
                <LogTable
                  entries={detail.session_log}
                  indexes={otherIdx}
                  cited={cited}
                />
              </details>
            </>
          )}
        </section>
      )}
          </div>
          <div>
      {result && (
        <section id="diagnosis">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-lg font-semibold">Diagnosis</h2>
            <span className="rounded-full border border-line-strong px-2 py-0.5 text-sm font-medium">
              {result.side ?? "no model output"}
            </span>
            {result.confidence !== null && (
              <span className={`text-sm ${muted}`}>
                {Math.round(confidence * 100)}% confident
              </span>
            )}
          </div>
          {result.confidence !== null && (
            <>
              <div
                className="mt-2 h-2 w-full max-w-xs rounded bg-line"
                role="img"
                aria-label={`confidence ${result.confidence}`}
              >
                <div
                  className="h-2 rounded bg-ink"
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
              <p className={`mt-1 text-sm ${muted}`}>
                Self-reported by the model, not a calibrated probability.
                Below the escalation threshold it forces human review — verify
                the side against the log and clauses before acting.
              </p>
            </>
          )}
          <p className="mt-2">{result.cause ?? "—"}</p>

          <h3 className="mt-4 font-medium">Evidence</h3>
          {result.evidence.length === 0 && (
            <p className={`text-sm ${muted}`}>No evidence cited.</p>
          )}
          <ul className="list-disc pl-5">
            {result.evidence.map((item, i) => (
              <li key={i}>
                {item.source}:{" "}
                {item.source === "log" ? (
                  <LogEvidenceRef itemRef={item.ref} logLength={logLength} />
                ) : (
                  item.ref
                )}{" "}
                {item.source === "reference" &&
                  (item.ref in result.verification ? (
                    result.verification[item.ref] ? (
                      <span className="text-sm text-ok-ink">
                        (verified)
                      </span>
                    ) : (
                      <span className="text-sm text-bad-ink">
                        (failed)
                      </span>
                    )
                  ) : (
                    <span className={`text-sm ${muted}`}>
                      (not among cited clauses)
                    </span>
                  ))}{" "}
                — {item.note}
              </li>
            ))}
          </ul>

          <h3 className="mt-4 font-medium">Clauses</h3>
          {Object.keys(result.verification).length === 0 ? (
            <p className={`text-sm ${muted}`}>
              No clauses cited — confident claims need corpus references.
            </p>
          ) : (
            <div className="mt-1 flex flex-wrap gap-2">
              {Object.entries(result.verification).map(([id, ok]) => (
                <span
                  key={id}
                  className={
                    ok
                      ? "rounded-full border border-ok/30 bg-ok-tint px-2 py-0.5 text-sm"
                      : "rounded-full border border-bad/30 bg-bad-tint px-2 py-0.5 text-sm"
                  }
                >
                  <StatusDot tone={ok ? "ok" : "bad"} />
                  {id} · {ok ? "verified" : "failed"}
                </span>
              ))}
            </div>
          )}

          <h3 className="mt-4 font-medium">Numbers (computed by code)</h3>
          {result.calc === null ? (
            <p className={`text-sm ${muted}`}>
              No calculation — the log has no usable meter data.
            </p>
          ) : (
            <dl className="mt-1 grid max-w-md grid-cols-2 gap-x-4 gap-y-1 text-sm tabular-nums">
              <dt className={muted}>Energy delivered</dt>
              <dd>{String(result.calc.energy_kwh)} kWh</dd>
              <dt className={muted}>Amount owed</dt>
              <dd>{String(result.calc.owed_kes)} KES</dd>
              <dt className={muted}>Refund</dt>
              <dd className="font-medium">
                {String(result.calc.refund_kes)} KES
              </dd>
              <dt className={muted}>Estimated</dt>
              <dd>{result.calc.estimated ? "yes" : "no"}</dd>
              <dt className={muted}>Underpaid</dt>
              <dd>{result.calc.underpaid ? "yes" : "no"}</dd>
              <dt className={muted}>Still open</dt>
              <dd>{String(result.still_open)}</dd>
            </dl>
          )}
          {result.technician_note && (
            <div className="mt-2 text-sm">
              <p>
                <span className="font-medium">Technician note: </span>
                {result.technician_note}
              </p>
              <p className={`mt-1 text-xs ${muted}`}>
                Model-written; any figures in it were filled in by code from
                the calculation above.
              </p>
            </div>
          )}

          {result.driver_message && (
            <div className="mt-3 rounded border border-line bg-surface p-3">
              <p className={`text-sm font-medium ${muted}`}>
                Driver message ({result.driver_message.language})
              </p>
              <p className="mt-1">{result.driver_message.text}</p>
              <p className={`mt-1 text-xs ${muted}`}>
                Figures in this message were filled in by code from the
                calculation above; the model wrote placeholders.
              </p>
            </div>
          )}

          {result.escalate ? (
            <div className="mt-3 rounded border border-bad/30 bg-bad-tint p-2">
              <p className="font-semibold">Needs human review</p>
              <ul className="list-disc pl-5">
                {result.escalate_reasons.map((r) => (
                  <li key={r}>
                    {r}{" "}
                    {reasonDetail(r) && (
                      <span className={`text-sm ${muted}`}>
                        {reasonDetail(r)}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            result.refund_draft && (
              <div className="mt-3 rounded border border-line bg-surface p-3">
                <p>
                  Refund draft: {result.refund_draft.amount_kes} KES
                  (requires approval)
                </p>
                {decision ? (
                  <div className="mt-1 rounded border border-ok/30 bg-ok-tint p-2">
                    <p>Recorded decision: {decision}</p>
                    <button
                      className="mt-1 text-sm underline focus-visible:outline-2 focus-visible:outline-offset-1"
                      onClick={() => setDecision(null)}
                    >
                      Record a different decision
                    </button>
                  </div>
                ) : (
                  <>
                    <label
                      htmlFor="decision-note"
                      className="mt-2 block text-sm font-medium"
                    >
                      Decision note (optional)
                    </label>
                    <input
                      id="decision-note"
                      className={`${field} mt-1 w-full`}
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                    <div className="mt-1 flex gap-2">
                      {confirming ? (
                        <>
                          <button
                            className={primary}
                            onClick={() => decide("approve")}
                            disabled={deciding}
                          >
                            {deciding
                              ? "Recording…"
                              : `Confirm ${result.refund_draft.amount_kes} KES refund`}
                          </button>
                          <button
                            className={`${field} px-3`}
                            onClick={() => setConfirming(false)}
                            disabled={deciding}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className={primary}
                            onClick={() => setConfirming(true)}
                          >
                            Approve
                          </button>
                          <button
                            className={`${field} px-3 disabled:opacity-50`}
                            onClick={() => decide("reject")}
                            disabled={deciding}
                          >
                            {deciding ? "Recording…" : "Reject"}
                          </button>
                        </>
                      )}
                    </div>
                  </>
                )}
              </div>
            )
          )}
        </section>
      )}
          </div>
        </div>
      )}
    </main>
  );
}
