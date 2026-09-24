"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { Compass, LogOut, Menu, User, X } from "lucide-react";
import { primaryNav } from "@/lib/constants/nav";
import { NavLink } from "@/components/navigation/NavLink";
import { PageContainer } from "@/components/layout/PageContainer";
import { IconButton } from "@/components/ui/IconButton";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils/cn";
import { useAuth } from "@/lib/auth/AuthContext";

function useVisibleNav() {
  const { user } = useAuth();

  return useMemo(() => {
    if (!user) return primaryNav;
    if (user.role === "provider") {
      return primaryNav.filter((item) => !["/trip", "/saved"].includes(item.href));
    }
    return primaryNav.filter((item) => item.href !== "/provider");
  }, [user]);
}

export function SiteHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const visibleNav = useVisibleNav();

  async function handleLogout() {
    await logout();
    setMobileOpen(false);
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-surface/90 backdrop-blur supports-[backdrop-filter]:bg-surface/75">
      <PageContainer className="flex h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 font-semibold text-ink">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-ink">
            <Compass className="size-4.5" aria-hidden="true" />
          </span>
          <span className="text-[17px] tracking-tight">LocaLens</span>
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
          {visibleNav.map((item) => (
            <NavLink key={item.href} {...item} />
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {isLoading ? null : user ? (
            <>
              <span className="max-w-[160px] truncate text-sm text-ink-muted" title={user.email}>
                {user.email}
              </span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="size-4" aria-hidden="true" />
                Log out
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  Log in
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="primary" size="sm">
                  <User className="size-4" aria-hidden="true" />
                  Get started
                </Button>
              </Link>
            </>
          )}
        </div>

        <IconButton
          label={mobileOpen ? "Close menu" : "Open menu"}
          className="md:hidden"
          aria-expanded={mobileOpen}
          aria-controls="mobile-nav-panel"
          onClick={() => setMobileOpen((open) => !open)}
        >
          {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </IconButton>
      </PageContainer>

      <div
        id="mobile-nav-panel"
        className={cn(
          "border-t border-line bg-surface md:hidden",
          mobileOpen ? "block" : "hidden",
        )}
      >
        <PageContainer className="flex flex-col gap-1 py-3">
          {visibleNav.map((item) => (
            <NavLink key={item.href} {...item} onClick={() => setMobileOpen(false)} />
          ))}
          <div className="mt-2 flex gap-2 border-t border-line pt-3">
            {isLoading ? null : user ? (
              <Button variant="outline" size="sm" className="w-full" onClick={handleLogout}>
                <LogOut className="size-4" aria-hidden="true" />
                Log out ({user.email})
              </Button>
            ) : (
              <>
                <Link href="/login" className="flex-1" onClick={() => setMobileOpen(false)}>
                  <Button variant="outline" size="sm" className="w-full">
                    Log in
                  </Button>
                </Link>
                <Link href="/register" className="flex-1" onClick={() => setMobileOpen(false)}>
                  <Button variant="primary" size="sm" className="w-full">
                    Get started
                  </Button>
                </Link>
              </>
            )}
          </div>
        </PageContainer>
      </div>
    </header>
  );
}
