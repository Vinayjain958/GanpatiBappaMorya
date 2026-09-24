import type { ReactNode } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { MobileTabBar } from "@/components/navigation/MobileTabBar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[60] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-ink"
      >
        Skip to main content
      </a>
      <SiteHeader />
      <main id="main-content" className="flex-1 pb-20 md:pb-0">
        {children}
      </main>
      <SiteFooter />
      <MobileTabBar />
    </div>
  );
}
