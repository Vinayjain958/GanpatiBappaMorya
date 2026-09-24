"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Eye, ListChecks, ShieldCheck, Sparkles } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Card, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { getMyExperiences, getMyProvider } from "@/lib/api/providers";
import type { ProviderMe } from "@/types/provider-api";
import type { ApiExperienceSummary } from "@/types/api";

const VERIFICATION_LABEL: Record<string, string> = {
  unverified: "Pending review",
  catalog_imported: "Imported from open data",
  verified: "Verified",
};

export function ProviderDashboard() {
  const [provider, setProvider] = useState<ProviderMe | null>(null);
  const [experiences, setExperiences] = useState<ApiExperienceSummary[]>([]);
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    Promise.all([getMyProvider(), getMyExperiences({ limit: 100 })])
      .then(([providerData, experiencesData]) => {
        if (cancelled) return;
        setProvider(providerData);
        setExperiences(experiencesData.items);
        setStatus("success");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  if (status === "loading") {
    return (
      <PageContainer className="space-y-6 py-8" aria-busy="true" aria-live="polite">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      </PageContainer>
    );
  }

  if (status === "error" || !provider) {
    return (
      <PageContainer className="py-8">
        <ErrorState
          title="Couldn't load your provider dashboard"
          onRetry={() => setReloadToken((t) => t + 1)}
        />
      </PageContainer>
    );
  }

  const activeCount = experiences.filter((e) => e.status === "active").length;
  const inactiveCount = experiences.filter((e) => e.status !== "active").length;

  return (
    <PageContainer className="space-y-8 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-accent">Provider</p>
          <h1 className="mt-1 flex items-center gap-2 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
            {provider.business_name}
            {provider.verification_status === "verified" ? (
              <Badge tone="success">
                <ShieldCheck className="size-3" aria-hidden="true" /> Verified
              </Badge>
            ) : null}
          </h1>
          <p className="text-sm text-ink-muted">
            {VERIFICATION_LABEL[provider.verification_status] ?? provider.verification_status}
            {provider.city ? ` · ${provider.city}` : ""}
          </p>
        </div>
        <Link href="/provider/experiences">
          <Button size="sm">Manage experiences</Button>
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardBody>
            <p className="flex items-center gap-1.5 text-xs text-ink-subtle">
              <ListChecks className="size-3.5" aria-hidden="true" /> Active listings
            </p>
            <p className="mt-1 text-2xl font-semibold text-ink">{activeCount}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="flex items-center gap-1.5 text-xs text-ink-subtle">
              <Eye className="size-3.5" aria-hidden="true" /> Inactive / draft listings
            </p>
            <p className="mt-1 text-2xl font-semibold text-ink">{inactiveCount}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="flex items-center gap-1.5 text-xs text-ink-subtle">
              <Sparkles className="size-3.5" aria-hidden="true" /> Analytics
            </p>
            <p className="mt-1 text-sm text-ink-muted">
              Analytics will appear once traveler interactions are enabled.
            </p>
          </CardBody>
        </Card>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-ink">Recent experiences</h2>
        {experiences.length === 0 ? (
          <p className="text-sm text-ink-muted">
            You haven&apos;t created any experiences yet.{" "}
            <Link href="/provider/experiences" className="font-medium text-accent hover:underline">
              Create your first one
            </Link>
            .
          </p>
        ) : (
          <ul className="space-y-2">
            {experiences.slice(0, 5).map((experience) => (
              <li
                key={experience.id}
                className="flex items-center justify-between rounded-lg border border-line bg-surface px-4 py-3 text-sm"
              >
                <span className="font-medium text-ink">{experience.title}</span>
                <Badge tone={experience.status === "active" ? "success" : "neutral"} className="capitalize">
                  {experience.status}
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </div>
    </PageContainer>
  );
}
