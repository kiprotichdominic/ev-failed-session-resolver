export default function Logo({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className="shrink-0"
    >
      <rect
        x="1"
        y="1"
        width="22"
        height="22"
        rx="6"
        fill="var(--color-accent)"
      />
      <path
        d="M13 5 6.5 13.5h4.7L11 19l6.5-8.5h-4.7L13 5z"
        fill="var(--color-accent-ink)"
      />
    </svg>
  );
}
