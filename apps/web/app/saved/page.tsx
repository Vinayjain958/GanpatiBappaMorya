import type { Metadata } from "next";
import Link from "next/link";
import { Bookmark } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { RequireRole } from "@/components/common/RequireRole";

export const metadata: Metadata = { title: "Saved" };

export default function SavedPage() {
  return (
    <RequireRole role="traveler">
      <PageContainer className="space-y-8 py-8 sm:py-10">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Saved
          </h1>
          <p className="text-sm leading-6 text-ink-muted">
            Experiences you&apos;ve bookmarked for later.
          </p>
        </div>

        <EmptyState
          icon={Bookmark}
          title="No saved experiences"
          description="Tap the bookmark icon on any experience card to save it here."
          action={
            <Link href="/discover">
              <Button size="sm">Browse experiences</Button>
            </Link>
          }
        />
      </PageContainer>
    </RequireRole>
  );
}