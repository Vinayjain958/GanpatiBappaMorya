import type { Metadata } from "next";
import { Hospital, Phone, ShieldAlert, Siren } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { EmergencyButton } from "@/components/safety/EmergencyButton";
import { SafetyResourceCard } from "@/components/safety/SafetyResourceCard";
import { DemoDataBadge } from "@/components/ui/DemoDataBadge";

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
        <DemoDataBadge label="Placeholder data" />
      </div>

      <EmergencyButton />

      <div className="grid gap-4 sm:grid-cols-2">
        <SafetyResourceCard
          icon={Hospital}
          title="Nearby hospitals"
          description="Resource lookup by location arrives in a later phase."
        />
        <SafetyResourceCard
          icon={Phone}
          title="Emergency contacts"
          description="Add trusted contacts to notify in an emergency."
        />
        <SafetyResourceCard
          icon={Siren}
          title="Local emergency numbers"
          description="Police, ambulance, and fire numbers for your current city."
        />
        <SafetyResourceCard
          icon={ShieldAlert}
          title="Safety alerts"
          description="Real-time area alerts are not yet connected."
        />
      </div>
    </PageContainer>
  );
}
