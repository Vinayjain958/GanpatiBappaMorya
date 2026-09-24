"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export function NavLink({
  href,
  label,
  icon: Icon,
  className,
  onClick,
}: {
  href: string;
  label: string;
  icon?: LucideIcon;
  className?: string;
  onClick?: () => void;
}) {
  const pathname = usePathname();
  const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));

  return (
    <Link
      href={href}
      onClick={onClick}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-ink-muted transition-colors",
        "hover:text-ink hover:bg-surface-sunken",
        isActive && "text-ink bg-surface-sunken",
        className,
      )}
    >
      {Icon ? <Icon className="size-4" aria-hidden="true" /> : null}
      {label}
    </Link>
  );
}
