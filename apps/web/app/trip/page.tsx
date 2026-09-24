import Link from "next/link";
import type { Metadata } from "next";
import { MapPinned } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { DemoDataBadge } from "@/components/ui/DemoDataBadge";
import { RequireRole } from "@/components/common/RequireRole";
import { mockTrip } from "@/mocks/trip";

export const metadata: Metadata = { title: "Trips" };

const hasTrip = true;

export default function TripListPage() {
  return (
    <RequireRole role="traveler">
      <PageContainer className="space-y-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">Your trips</h1>
            <p className="text-sm text-ink-muted">Plans LocaLens has put together for you.</p>
          </div>
          <DemoDataBadge />
        </div>

        {hasTrip ? (
          <Link href={`/trip/${mockTrip.id}`}>
            <Card className="transition-shadow hover:shadow-[0_16px_32px_-16px_rgba(11,18,32,0.25)]">
              <CardBody className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="font-semibold text-ink">{mockTrip.title}</p>
                  <p className="text-sm text-ink-muted">{mockTrip.contextSummary}</p>
                </div>
                <span className="text-sm font-medium text-accent">View plan &rarr;</span>
              </CardBody>
            </Card>
          </Link>
        ) : (
          <EmptyState
            icon={MapPinned}
            title="No trip created yet"
            description="Describe what you want on the Discover page and LocaLens will start building a plan."
            action={
              <Link href="/discover">
                <Button size="sm">Start discovering</Button>
              </Link>
            }
          />
        )}
      </PageContainer>
    </RequireRole>
  );
}
