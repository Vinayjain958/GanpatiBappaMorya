import type { Metadata } from "next";
import { Activity, BarChart3, Clock, TrendingUp, Users } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { InsightStatCard } from "@/components/provider/InsightStatCard";
import { InsightPlaceholderChart } from "@/components/provider/InsightPlaceholderChart";
import { DemoDataBadge } from "@/components/ui/DemoDataBadge";
import { mockProviderInsights } from "@/mocks/provider";

export const metadata: Metadata = { title: "Provider insights" };

export default function ProviderInsightsPage() {
  return (
    <PageContainer className="space-y-6 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">Insights</h1>
          <p className="text-sm text-ink-muted">
            Demand intelligence. Provider analytics backend is not yet implemented &mdash; values
            below are illustrative.
          </p>
        </div>
        <DemoDataBadge />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {mockProviderInsights.map((stat) => (
          <InsightStatCard key={stat.id} stat={stat} />
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <InsightPlaceholderChart
          icon={TrendingUp}
          title="Demand trend"
          description="Views, saves, and bookings over time."
        />
        <InsightPlaceholderChart
          icon={Clock}
          title="Peak hours"
          description="When travelers are most interested."
        />
        <InsightPlaceholderChart
          icon={Users}
          title="Traveler interests"
          description="Which traveler types engage most."
        />
        <InsightPlaceholderChart
          icon={Activity}
          title="Conversion trend"
          description="View-to-save and save-to-booking rates."
        />
      </div>

      <div className="flex items-center gap-2 rounded-lg border border-line bg-surface-sunken/50 p-4 text-sm text-ink-muted">
        <BarChart3 className="size-4 shrink-0" aria-hidden="true" />
        Provider Intelligence is a planned capability (Phase 10). Nothing on this page reflects
        live platform data.
      </div>
    </PageContainer>
  );
}
