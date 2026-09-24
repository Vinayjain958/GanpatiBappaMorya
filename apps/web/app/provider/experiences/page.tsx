"use client";

import Link from "next/link";
import { Plus } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/Button";
import { RequireRole } from "@/components/common/RequireRole";
import { ProviderExperiencesManager } from "./ProviderExperiencesManager";

export default function ProviderExperiencesPage() {
  return (
    <RequireRole role="provider">
      <PageContainer className="space-y-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">Your experiences</h1>
            <p className="text-sm text-ink-muted">Manage listings, pricing, and availability.</p>
          </div>
          <Link href="/provider/experiences/new">
            <Button size="sm">
              <Plus className="size-4" aria-hidden="true" />
              New experience
            </Button>
          </Link>
        </div>

        <ProviderExperiencesManager />
      </PageContainer>
    </RequireRole>
  );
}
