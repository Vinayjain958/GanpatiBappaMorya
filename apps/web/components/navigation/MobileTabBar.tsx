"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { primaryNav } from "@/lib/constants/nav";
import { cn } from "@/lib/utils/cn";

export function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/80 md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <ul className="grid grid-cols-5">
        {primaryNav.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href);
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium text-ink-subtle",
                  isActive && "text-accent",
                )}
              >
                <Icon className="size-5" aria-hidden="true" />
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
