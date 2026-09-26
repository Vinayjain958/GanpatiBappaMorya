"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { primaryNav } from "@/lib/constants/nav";
import { cn } from "@/lib/utils/cn";

export function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary mobile"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface/90 px-2 pt-1.5 shadow-float backdrop-blur-xl md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <ul className="mx-auto grid max-w-xl grid-cols-5 gap-1">
        {primaryNav.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href);

          return (
            <li key={href} className="min-w-0">
              <Link
                href={href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl px-1 py-1.5 text-[10px] font-medium transition-all duration-150",
                  isActive
                    ? "border border-accent/60 bg-accent-soft font-semibold text-ink shadow-xs"
                    : "text-ink-muted hover:bg-surface-sunken/60 hover:text-ink",
                )}
              >
                <Icon className="size-4.5" aria-hidden="true" />
                <span className="whitespace-nowrap">{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}