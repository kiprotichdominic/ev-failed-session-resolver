import Link from "next/link";
import Logo from "./logo";
import NavLinks from "./nav-links";

export function SidebarFallback() {
  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col gap-6 border-r border-line px-5 py-6 lg:flex">
      <span className="flex items-center gap-2 text-base font-semibold leading-snug tracking-tight">
        <Logo size={24} />
        EV-Failed-Session Resolver
      </span>
      <NavLinks vertical />
    </aside>
  );
}

export default function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col gap-6 border-r border-line bg-surface/40 px-5 py-6 lg:flex">
      <Link
        href="/"
        className="flex items-center gap-2 text-base font-semibold leading-snug tracking-tight hover:text-accent focus-visible:outline-2 focus-visible:outline-offset-4"
      >
        <Logo size={24} />
        EV-Failed-Session Resolver
      </Link>
      <NavLinks vertical />
    </aside>
  );
}
