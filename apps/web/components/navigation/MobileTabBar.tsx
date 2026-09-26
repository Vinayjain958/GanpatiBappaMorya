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
      className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-pastel-mint px-2 pt-1.5 md:hidden"
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
                  "flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[10px] font-semibold transition-colors",
                  isActive
                    ? "bg-surface text-ink shadow-sm"
                    : "text-ink/70 hover:bg-surface/40 hover:text-ink",
                )}
              >
                <Icon className="size-5" aria-hidden="true" />
                <span className="whitespace-nowrap">{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}