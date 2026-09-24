"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { Bookmark, Clock, MapPin, ShieldCheck, Star } from "lucide-react";
import type { Experience } from "@/types/experience";
import { Badge } from "@/components/ui/Badge";
import { PersonalizationBadge } from "@/components/ui/PersonalizationBadge";
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
  const [isSaved, setIsSaved] = useState(saved);
  const isCompact = variant === "compact";
  const isFeatured = variant === "featured";

  function handleSaveToggle() {
    setIsSaved((prev) => !prev);
    onToggleSave?.(experience.id);
  }

  return (
    <article
      className={cn(
        "group relative flex overflow-hidden rounded-xl border border-line bg-surface shadow-[0_1px_2px_rgba(11,18,32,0.04)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_32px_-16px_rgba(11,18,32,0.25)]",
        isCompact ? "flex-row items-stretch" : "flex-col",
        isFeatured && "sm:col-span-2",
        className,
      )}
    >
      <div
        className={cn(
          "relative shrink-0 overflow-hidden bg-surface-sunken",
          isCompact ? "w-28 sm:w-36" : "aspect-[4/3] w-full",
          isFeatured && "sm:aspect-auto sm:min-h-[220px]",
        )}
      >
        <Image
          src={experience.imageUrl}
          alt=""
          fill
          sizes={isCompact ? "144px" : "(min-width: 640px) 400px, 100vw"}
          className="object-cover transition-transform duration-300 group-hover:scale-105"
        />
        {!isCompact ? (
          <button
            type="button"
            onClick={handleSaveToggle}
            aria-pressed={isSaved}
            aria-label={isSaved ? "Remove from saved" : "Save experience"}
            className="absolute right-2.5 top-2.5 inline-flex size-9 items-center justify-center rounded-full bg-surface/90 text-ink shadow-sm backdrop-blur transition-colors hover:text-accent"
          >
            <Bookmark className={cn("size-4.5", isSaved && "fill-accent text-accent")} aria-hidden="true" />
          </button>
        ) : null}
      </div>

      <div className={cn("flex flex-1 flex-col gap-2.5 p-4", isCompact && "py-3")}>
        <div className="flex items-start justify-between gap-2">
          <Badge tone="accent">{experience.categoryLabel}</Badge>
          {!isCompact ? (
            <Badge tone={availabilityTone[experience.availability]}>
              {availabilityLabel[experience.availability]}
            </Badge>
          ) : null}
        </div>

        <div>
          <h3 className={cn("font-semibold text-ink", isCompact ? "text-sm" : "text-base")}>
            <Link href={`/discover/${experience.id}`} className="hover:underline">
              <span className="absolute inset-0" aria-hidden={isCompact} />
              {experience.title}
            </Link>
          </h3>
          {!isCompact ? (
            <>
              <p className="mt-1 line-clamp-2 text-sm text-ink-muted">{experience.shortDescription}</p>
              {experience.matchSignals && experience.matchSignals.length > 0 ? (
                <div className="mt-2">
                  <PersonalizationBadge signals={experience.matchSignals} />
                </div>
              ) : null}
            </>
          ) : null}
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-subtle">
          <span className="inline-flex items-center gap-1">
            <MapPin className="size-3.5" aria-hidden="true" />
            {experience.location.area}
            {experience.distanceKm != null ? ` · ${experience.distanceKm} km` : ""}
          </span>
          {experience.travelTimeMinutes != null ? (
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3.5" aria-hidden="true" />
              {Math.round(experience.travelTimeMinutes)} min
              {experience.travelTimeSource === "haversine_estimate" ? " (est.)" : ""}
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

        <div className="flex items-center justify-between border-t border-line pt-2.5">
          {experience.rating != null ? (
            <span className="inline-flex items-center gap-1 text-xs text-ink-muted">
              <Star className="size-3.5 fill-highlight text-highlight" aria-hidden="true" />
              <span className="font-medium text-ink">{experience.rating}</span>
              {experience.reviewCount != null ? <span>({experience.reviewCount})</span> : null}
            </span>
          ) : (
            <span className="text-xs text-ink-subtle">No ratings yet</span>
          )}
          <span className="text-sm font-semibold text-ink">
            {experience.priceInr === 0 ? "Free" : `₹${experience.priceInr}`}
            {experience.isPriceEstimated ? <span className="text-ink-subtle"> est.</span> : null}
          </span>
        </div>
      </div>
    </article>
  );
}
