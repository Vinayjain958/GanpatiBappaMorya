"use client";

import Link from "next/link";
import { useState } from "react";
import { Bookmark, Clock, MapPin, ShieldCheck, Star } from "lucide-react";
import type { Experience } from "@/types/experience";
import { Badge } from "@/components/ui/Badge";
import { PersonalizationBadge } from "@/components/ui/PersonalizationBadge";
import { ExperienceImageView } from "@/components/experience/ExperienceImageView";
import { ScrollReveal } from "@/components/common/ScrollReveal";
import { feedbackApi } from "@/lib/api/feedback";
import { cn } from "@/lib/utils/cn";

const availabilityTone = {
  available: "success",
  limited: "warning",
  unavailable: "danger",
} as const;

const availabilityLabel = {
  available: "Available",
  limited: "Limited spots",
  unavailable: "Unavailable",
} as const;

export interface ExperienceCardProps {
  experience: Experience;
  variant?: "standard" | "compact" | "featured";
  saved?: boolean;
  onToggleSave?: (id: string) => void;
  className?: string;
}

export function ExperienceCard({
  experience,
  variant = "standard",
  saved = false,
  onToggleSave,
  className,
}: ExperienceCardProps) {
  // `saved` arrives from an async fetch (useSavedExperienceIds) that
  // resolves after this card's first render, so the prop itself is the
  // source of truth rather than something copied into local state via an
  // effect. `optimisticSaved` only overrides it for the brief window
  // between a click and that write actually confirming/failing — cleared
  // whenever the prop's value already agrees with the pending optimistic
  // one, so a later real `saved` prop update (e.g. this list refetching)
  // is never masked by a stale override.
  const [optimisticSaved, setOptimisticSaved] = useState<boolean | null>(null);
  const isSaved = optimisticSaved ?? saved;
  const isCompact = variant === "compact";
  const isFeatured = variant === "featured";

  async function handleSaveToggle() {
    const nextSaved = !isSaved;
    // Optimistic: the button responds instantly, and rolls back only if
    // the write actually fails — matches FeedbackControls.tsx's pattern
    // for the same SAVE/UNSAVE interaction used on the detail page, so
    // saving from either the Discover grid or the detail page persists
    // to the same per-traveler backend state (GET /experiences/saved).
    setOptimisticSaved(nextSaved);
    onToggleSave?.(experience.id);
    try {
      await feedbackApi.recordInteraction({
        experience_id: experience.id,
        event_type: nextSaved ? "SAVE" : "UNSAVE",
        client_event_id: `${experience.id}-${nextSaved ? "SAVE" : "UNSAVE"}-${Date.now()}`,
      });
    } catch (err) {
      console.error("Failed to record save/unsave interaction:", err);
      setOptimisticSaved(!nextSaved);
    }
  }

  return (
    <ScrollReveal>
      <article
        className={cn(
          "group relative flex overflow-hidden rounded-2xl porcelain-card",
          isCompact ? "flex-row items-stretch" : "flex-col",
          isFeatured && "sm:col-span-2",
          className,
        )}
      >
        <div
          className={cn(
            "relative shrink-0 overflow-hidden bg-pastel-sky/20",
            isCompact ? "w-28 sm:w-36" : "aspect-[4/3] w-full",
            isFeatured && "sm:aspect-auto sm:min-h-[220px]",
          )}
        >
          <ExperienceImageView
            src={experience.imageUrl}
            alt=""
            fill
            sizes={isCompact ? "144px" : "(min-width: 640px) 400px, 100vw"}
            className="object-cover transition-transform duration-500 ease-out group-hover:scale-105"
          />

          {/* Subtle atmospheric scrim */}
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent opacity-60" />

          {!isCompact ? (
            <button
              type="button"
              onClick={handleSaveToggle}
              aria-pressed={isSaved}
              aria-label={isSaved ? "Remove from saved" : "Save experience"}
              className="absolute right-3 top-3 z-20 inline-flex size-9 items-center justify-center rounded-full border border-white/60 bg-surface/90 text-ink shadow-sm backdrop-blur-md transition-all duration-200 hover:scale-110 hover:bg-pastel-rose/80 active:scale-95"
            >
              <Bookmark
                className={cn(
                  "size-4",
                  isSaved && "fill-accent text-accent",
                )}
                aria-hidden="true"
              />
            </button>
          ) : null}

          {!isCompact && !experience.image.isFallback && !experience.image.isPlaceSpecific ? (
            <span className="absolute bottom-2 left-2.5 z-10 rounded-md border border-line/50 bg-surface/85 px-1.5 py-0.5 text-[10px] italic text-ink-subtle backdrop-blur-sm">
              Representative image
            </span>
          ) : null}
        </div>

        <div className={cn("flex flex-1 flex-col gap-3 p-4 sm:p-5", isCompact && "py-3")}>
          <div className="flex items-start justify-between gap-2">
            <Badge tone="accent">{experience.categoryLabel}</Badge>
            {!isCompact ? (
              <Badge tone={availabilityTone[experience.availability]}>
                {availabilityLabel[experience.availability]}
              </Badge>
            ) : null}
          </div>

          <div>
            <h3
              className={cn(
                "font-semibold leading-snug tracking-tight text-ink transition-colors group-hover:text-accent",
                isCompact ? "text-sm" : "text-base",
              )}
            >
              <Link href={`/discover/${experience.id}`} className="hover:underline">
                <span className="absolute inset-0 z-10" aria-hidden={isCompact} />
                {experience.title}
              </Link>
            </h3>

            {!isCompact ? (
              <>
                <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-ink-muted">
                  {experience.shortDescription}
                </p>

                {experience.matchSignals &&
                experience.matchSignals.length > 0 ? (
                  <div className="mt-2">
                    <PersonalizationBadge signals={experience.matchSignals} />
                  </div>
                ) : null}
              </>
            ) : null}
          </div>

          <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-ink-subtle">
            <span className="inline-flex items-center gap-1">
              <MapPin className="size-3.5 text-accent" aria-hidden="true" />
              {experience.location.area}
              {experience.distanceKm != null
                ? ` · ${experience.distanceKm} km`
                : ""}
            </span>

            {experience.travelTimeMinutes != null ? (
              <span className="inline-flex items-center gap-1">
                <Clock className="size-3.5" aria-hidden="true" />
                {Math.round(experience.travelTimeMinutes)} min
                {experience.travelTimeSource === "haversine_estimate"
                  ? " (est.)"
                  : ""}
              </span>
            ) : null}

            {experience.durationMinutes != null ? (
              <span className="inline-flex items-center gap-1">
                <Clock className="size-3.5" aria-hidden="true" />
                {experience.durationMinutes} min
              </span>
            ) : null}

            {experience.accessibility.wheelchairAccessible ? (
              <span className="inline-flex items-center gap-1">
                <ShieldCheck className="size-3.5" aria-hidden="true" />
                Accessible
              </span>
            ) : null}
          </div>

          <div className="flex items-center justify-between border-t border-line pt-3">
            {experience.rating != null ? (
              <span className="inline-flex items-center gap-1 text-xs text-ink-muted">
                <Star
                  className="size-3.5 fill-highlight text-highlight"
                  aria-hidden="true"
                />
                <span className="font-semibold tabular-nums text-ink">{experience.rating}</span>
                {experience.reviewCount != null ? (
                  <span className="tabular-nums">({experience.reviewCount})</span>
                ) : null}
                {experience.isSynthetic ? (
                  <span
                    className="ml-0.5 rounded-md border border-line bg-surface-sunken/60 px-1.5 py-0.5 text-[9px] font-medium text-ink-subtle"
                    title="Synthetic Demo Rating"
                  >
                    Demo
                  </span>
                ) : null}
              </span>
            ) : (
              <span className="text-xs text-ink-subtle">No ratings yet</span>
            )}

            <span className="text-sm font-semibold tabular-nums text-ink">
              {experience.priceInr === 0
                ? "Free"
                : `₹${experience.priceInr}`}
              {experience.isPriceEstimated ? (
                <span className="font-normal text-ink-subtle"> est.</span>
              ) : null}
            </span>
          </div>
        </div>
      </article>
    </ScrollReveal>
  );
}
