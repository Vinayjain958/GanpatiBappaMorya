import type { Metadata } from "next";
import { ShieldAlert } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { EmergencyButton } from "@/components/safety/EmergencyButton";
import { SafetyDashboard } from "@/components/safety/SafetyDashboard";

export const metadata: Metadata = { title: "Safety" };

export default function SafetyPage() {
  return (
    <PageContainer className="space-y-8 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
            <ShieldAlert className="size-7 text-danger" aria-hidden="true" />
            Safety Center
          </h1>
          <p className="text-sm text-ink-muted">
            Kept separate from recommendations &mdash; this stays available even if discovery is down.
          </p>
        </div>
      </div>

      <EmergencyButton />

      <SafetyDashboard />
    </PageContainer>
  );
}
