import type { Metadata } from "next";
import { PageContainer } from "@/components/layout/PageContainer";
import { ProviderInsightsDashboard } from "@/components/provider/ProviderInsightsDashboard";

export const metadata: Metadata = { title: "Provider insights" };

export default function ProviderInsightsPage() {
  return (
    <PageContainer className="space-y-6 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">Insights</h1>
          <p className="text-sm text-ink-muted">
            Demand intelligence and provider analytics.
          </p>
        </div>
      </div>

      <ProviderInsightsDashboard />
    </PageContainer>
  );
}
