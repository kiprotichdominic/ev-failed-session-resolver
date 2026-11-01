"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Metric = {
  values: (number | null)[];
  min: number | null;
  max: number | null;
};
type Payload = {
  split: string;
  runs: number;
  num_cases: number;
  metrics: Record<string, Metric>;
  failures: { case_id: string; field: string; expected: unknown; got: unknown }[];
};

function MetricsTable({ title, payload }: { title: string; payload: Payload }) {
  return (
    <div>
      <h3 className="font-semibold">{title}</h3>
      <div className="overflow-x-auto">
      <table className="mt-1 w-full border-collapse text-sm tabular-nums">
        <thead>
          <tr className="border-b border-line text-left">
            <th className="pr-2">metric</th>
            <th className="pr-2">values</th>
            <th className="pr-2">min</th>
            <th>max</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(payload.metrics).map(([name, spec]) => (
            <tr key={name}>
              <td className="pr-2">{name}</td>
              <td className="pr-2">{JSON.stringify(spec.values)}</td>
              <td className="pr-2">{JSON.stringify(spec.min)}</td>
              <td>{JSON.stringify(spec.max)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}

const SHARE_METRICS = [
  "side_accuracy",
  "clause_match",
  "citation_pass_rate",
  "escalation_precision",
  "escalation_recall",
  "refund_correct",
];

function total(values: (number | null)[]): number {
  return values.reduce((s: number, v) => s + (v ?? 0), 0);
}

function mean(values: (number | null)[]): number | null {
  const xs = values.filter((v): v is number => v !== null);
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
}

function fmt(v: number | null): string {
  return v === null ? "n/a" : v.toFixed(2);
}

function VerdictStrip({
  results,
  baseline,
}: {
  results: Payload;
  baseline: Payload | null;
}) {
  const side = mean(results.metrics["side_accuracy"]?.values ?? []);
  const refund = mean(results.metrics["refund_correct"]?.values ?? []);
  const hcw = results.metrics["high_confidence_wrong"];
  let wins = 0;
  let totalPairs = 0;
  if (baseline) {
    for (const name of SHARE_METRICS) {
      const a = mean(results.metrics[name]?.values ?? []);
      const b = mean(baseline.metrics[name]?.values ?? []);
      if (a === null || b === null) continue;
      totalPairs += 1;
      if (a > b) wins += 1;
    }
  }
  return (
    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 rounded border border-line p-2 text-sm tabular-nums">
      <span>
        side_accuracy <span className="font-medium">{fmt(side)}</span>
      </span>
      <span>
        refund_correct <span className="font-medium">{fmt(refund)}</span>
      </span>
      <span>
        high-confidence wrong{" "}
        <span className="font-medium">
          {hcw ? total(hcw.values) : "n/a"}
        </span>
      </span>
      {baseline && totalPairs > 0 && (
        <span>
          beats baseline{" "}
          <span className="font-medium">
            {wins}/{totalPairs}
          </span>{" "}
          share metrics
        </span>
      )}
    </div>
  );
}

function Bar({ value, className }: { value: number | null; className: string }) {
  return (
    <div className="h-2 rounded bg-line">
      {value !== null && (
        <div
          className={`h-2 rounded ${className}`}
          style={{ width: `${value * 100}%` }}
        />
      )}
    </div>
  );
}

function CompareBars({
  results,
  baseline,
}: {
  results: Payload;
  baseline: Payload | null;
}) {
  const hcw = results.metrics["high_confidence_wrong"];
  const hcwBase = baseline?.metrics["high_confidence_wrong"];
  return (
    <div className="mt-3">
      <h3 className="font-semibold">Model vs baseline (mean across runs)</h3>
      <p className="mt-1 flex gap-4 text-sm">
        <span>
          <span
            aria-hidden="true"
            className="mr-1 inline-block h-2 w-4 rounded bg-ink"
          />
          Model
        </span>
        {baseline && (
          <span>
            <span
              aria-hidden="true"
              className="mr-1 inline-block h-2 w-4 rounded bg-faint"
            />
            Baseline
          </span>
        )}
      </p>
      {SHARE_METRICS.map((name) => {
        const a = mean(results.metrics[name]?.values ?? []);
        const b = baseline ? mean(baseline.metrics[name]?.values ?? []) : null;
        return (
          <div key={name} className="mt-2">
            <div className="flex gap-2 text-sm">
              <span>{name}</span>
              <span className="tabular-nums">
                {fmt(a)}
                {baseline && ` vs ${fmt(b)}`}
                {baseline && a !== null && b !== null && (
                  <span
                    className={
                      a > b
                        ? "text-ok-ink"
                        : a < b
                          ? "text-bad-ink"
                          : "text-muted"
                    }
                  >
                    {a > b
                      ? ` (+${(a - b).toFixed(2)})`
                      : a < b
                        ? ` (${(a - b).toFixed(2)})`
                        : " (±0.00)"}
                  </span>
                )}
              </span>
            </div>
            <div className="mt-1">
              <Bar value={a} className="bg-ink" />
            </div>
            {baseline && (
              <div className="mt-1">
                <Bar value={b} className="bg-faint" />
              </div>
            )}
          </div>
        );
      })}
      {hcw && (
        <p className="mt-2 text-sm">
          High-confidence wrong (lower is better): model{" "}
          <span className="tabular-nums">
            {JSON.stringify(hcw.values)} (total {total(hcw.values)})
          </span>
          {hcwBase && (
            <>
              {" "}
              · baseline{" "}
              <span className="tabular-nums">
                {JSON.stringify(hcwBase.values)} (total{" "}
                {total(hcwBase.values)})
              </span>
            </>
          )}
        </p>
      )}
    </div>
  );
}

export default function EvaluationPage() {
  const [results, setResults] = useState<Payload | null>(null);
  const [baseline, setBaseline] = useState<Payload | null>(null);
  const [missing, setMissing] = useState(false);
  const [error, setError] = useState(false);

  function load() {
    setMissing(false);
    setError(false);
    fetch(`${API}/api/results`)
      .then((r) => {
        if (r.ok) return r.json();
        if (r.status === 404) {
          setMissing(true);
          return null;
        }
        throw new Error(String(r.status));
      })
      .then((d) => {
        if (d) setResults(d);
      })
      .catch(() => setError(true));
    fetch(`${API}/api/baseline`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setBaseline(d))
      .catch(() => null);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="mx-auto w-full max-w-6xl px-6 pt-6">
      <h1 className="text-2xl font-bold tracking-tight">Evaluation</h1>
      <p className="mt-1 text-sm text-muted">
        Model vs code-only baseline on the human-written dev/held-out labels.
      </p>
      {error && (
        <p role="alert" className="mt-2 text-bad-ink">
          Could not reach the API. Is it running?
        </p>
      )}
      {!error && missing && (
        <div className="mt-2">
          <p>No results yet. To generate them:</p>
          <pre className="mt-1 overflow-x-auto border border-line bg-surface p-2 font-mono text-xs">
{`# 1. add cases + eval/labels.json (human-written)
python eval/run_eval.py --split dev --runs 3 --client fake
python eval/baseline.py --split dev --runs 3
# 2. press Check again below`}
          </pre>
          <button
            className="mt-2 border border-line-strong px-2 py-0.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-1"
            onClick={load}
          >
            Check again
          </button>
        </div>
      )}
      {results && (
        <>
          <p className="mt-2">
            Split: {results.split}, runs: {results.runs}, cases:{" "}
            {results.num_cases}
          </p>
          <VerdictStrip results={results} baseline={baseline} />
          <CompareBars results={results} baseline={baseline} />
          <div
            className={baseline ? "mt-3 grid gap-6 md:grid-cols-2" : "mt-3"}
          >
            <MetricsTable title="Model" payload={results} />
            {baseline && <MetricsTable title="Baseline" payload={baseline} />}
          </div>
          <h2 className="mt-4 text-lg font-semibold">Failures</h2>
          {results.failures.length === 0 && <p>No failures recorded.</p>}
          <ul className="list-disc pl-5">
            {results.failures.map((f, i) => (
              <li key={i}>
                {f.case_id} / {f.field}: expected{" "}
                <code className="font-mono">{JSON.stringify(f.expected)}</code>
                , got{" "}
                <code className="font-mono">{JSON.stringify(f.got)}</code>
              </li>
            ))}
          </ul>
          <details className="mt-4">
            <summary className="cursor-pointer text-sm hover:underline">
              What these metrics mean
            </summary>
            <ul className="mt-1 space-y-1 text-sm">
              <li>
                <span className="font-medium">side_accuracy</span>
                <span className="text-muted">
                  : share of cases with the right at-fault side (a model
                  failure counts as wrong).
                </span>
              </li>
              <li>
                <span className="font-medium">clause_match</span>
                <span className="text-muted">
                  : share where the cited clause set exactly equals the
                  label&apos;s.
                </span>
              </li>
              <li>
                <span className="font-medium">citation_pass_rate</span>
                <span className="text-muted">
                  : share of cases without an unverified citation.
                </span>
              </li>
              <li>
                <span className="font-medium">
                  escalation_precision, escalation_recall
                </span>
                <span className="text-muted">
                  : with escalated as the positive class; null when undefined.
                </span>
              </li>
              <li>
                <span className="font-medium">refund_correct</span>
                <span className="text-muted">
                  : share where the draft amount matches, or both are null.
                </span>
              </li>
              <li>
                <span className="font-medium">high_confidence_wrong</span>
                <span className="text-muted">
                  : wrong-side cases at confidence 0.8 or above (lower is
                  better).
                </span>
              </li>
            </ul>
          </details>
        </>
      )}
    </main>
  );
}
