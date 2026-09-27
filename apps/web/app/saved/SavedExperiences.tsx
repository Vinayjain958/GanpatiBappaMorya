"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Bookmark } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { ExperienceCard } from "@/components/experience/ExperienceCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";
import { listSavedExperiences } from "@/lib/api/experiences";
import { mapApiExperienceToUi } from "@/lib/api/experienceAdapter";
import { ApiError } from "@/lib/api/client";
import type { Experience } from "@/types/experience";

type Status = "loading" | "success" | "error";

export function SavedExperiences() {
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    listSavedExperiences(controller.signal)
      .then((response) => {
        if (controller.signal.aborted) return;
        setExperiences(response.items.map((item) => mapApiExperienceToUi(item)));
        setStatus("success");
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.status === 0) return; // aborted fetch
        setStatus("error");
      });

    return () => controller.abort();
  }, [reloadToken]);

  function handleUnsave(id: string) {
    // The card already recorded the UNSAVE interaction itself — just drop
    // it from this list immediately rather than waiting for a refetch.
    setExperiences((prev) => prev.filter((experience) => experience.id !== id));
  }

  return (
    <PageContainer className="space-y-8 py-8 sm:py-10">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">Saved</h1>
        <p className="text-sm leading-6 text-ink-muted">
          Experiences you&apos;ve bookmarked for later.
        </p>
      </div>

      {status === "loading" ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-72 w-full rounded-2xl" />
          ))}
        </div>
      ) : status === "error" ? (
        <ErrorState
          title="Couldn't load your saved experiences"
          description="Please try again."
          onRetry={() => {
            setStatus("loading");
            setReloadToken((prev) => prev + 1);
          }}
        />
      ) : experiences.length === 0 ? (
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
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {experiences.map((experience) => (
            <ExperienceCard
              key={experience.id}
              experience={experience}
              saved
              onToggleSave={handleUnsave}
            />
          ))}
        </div>
      )}
    </PageContainer>
  );
}
