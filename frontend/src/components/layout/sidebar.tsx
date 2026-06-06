"use client";

import { LayoutDashboard, Plus, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export const studioNavItems = [
  { href: "/universes", label: "Universes", icon: LayoutDashboard },
  { href: "/universes/new", label: "Create", icon: Plus },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden min-h-screen w-72 shrink-0 border-r border-white/10 bg-black/45 px-4 py-5 backdrop-blur-xl lg:block">
      <Link href="/" className="flex items-center gap-3 px-2">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-sky-200">
          <Sparkles className="h-4 w-4" />
        </span>
        <span>
          <span className="block text-sm font-semibold text-white">Universe Studio</span>
          <span className="block text-xs text-slate-500">Create worlds, not clips.</span>
        </span>
      </Link>

      <nav className="mt-8 space-y-1">
        {studioNavItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;

          return (
            <Link
              key={`${item.label}-${item.href}`}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 transition",
                active
                  ? "border border-white/10 bg-white/[0.08] text-white"
                  : "hover:bg-white/[0.05] hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
