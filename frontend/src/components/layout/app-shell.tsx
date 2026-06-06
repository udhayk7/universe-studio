"use client";

import { Menu, Plus, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Sidebar, studioNavItems } from "@/components/layout/sidebar";
import { ButtonLink } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#050507] text-white">
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.16),transparent_45%),linear-gradient(180deg,#050507_0%,#090a12_52%,#050507_100%)]" />
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-40 border-b border-white/10 bg-black/45 backdrop-blur-xl">
            <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
              <Link href="/" className="flex min-w-0 items-center gap-3 lg:hidden">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-sky-200">
                  <Sparkles className="h-4 w-4" />
                </span>
                <span className="truncate text-sm font-semibold">Universe Studio</span>
              </Link>
              <button
                onClick={() => setMobileNavOpen((value) => !value)}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.06] text-slate-300 lg:hidden"
                type="button"
                aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
              >
                <Menu className="h-4 w-4" />
              </button>
              <div className="hidden min-w-0 lg:block">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Studio</p>
                <p className="mt-1 text-sm text-slate-300">Persistent cinematic universes</p>
              </div>
              <ButtonLink href="/universes/new" size="sm" className="hidden sm:inline-flex">
                <Plus className="h-4 w-4" />
                Create Universe
              </ButtonLink>
            </div>
            {mobileNavOpen ? (
              <nav className="border-t border-white/10 px-4 py-3 lg:hidden">
                <div className="grid gap-2">
                  {studioNavItems.map((item) => {
                    const Icon = item.icon;
                    const active = pathname === item.href;

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMobileNavOpen(false)}
                        className={cn(
                          "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                          active
                            ? "border border-white/10 bg-white/[0.08] text-white"
                            : "text-slate-400 hover:bg-white/[0.05] hover:text-white",
                        )}
                      >
                        <Icon className="h-4 w-4" />
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              </nav>
            ) : null}
          </header>
          <main className="flex-1 px-4 py-8 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
