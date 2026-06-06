import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";
import { ButtonLink } from "@/components/ui/button";

export function Navbar() {
  return (
    <header className="fixed left-0 right-0 top-0 z-50 border-b border-white/10 bg-black/45 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-sky-200">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="text-sm font-semibold tracking-wide text-white">Universe Studio</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
          <Link href="/#problem" className="transition hover:text-white">
            Problem
          </Link>
          <Link href="/#features" className="transition hover:text-white">
            Features
          </Link>
          <Link href="/#demo" className="transition hover:text-white">
            Demo
          </Link>
        </nav>
        <ButtonLink href="/universes/new" size="sm">
          Create
          <ArrowRight className="h-4 w-4" />
        </ButtonLink>
      </div>
    </header>
  );
}
