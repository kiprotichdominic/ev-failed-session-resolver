export default function StatusDot({ tone }: { tone: "ok" | "bad" | "idle" }) {
  const color =
    tone === "ok"
      ? "bg-ok"
      : tone === "bad"
        ? "bg-bad"
        : "bg-idle";
  return (
    <span
      aria-hidden="true"
      className={`mr-1 inline-block h-2 w-2 rounded-full ${color}`}
    />
  );
}
