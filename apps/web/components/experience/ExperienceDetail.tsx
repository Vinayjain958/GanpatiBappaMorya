"use client";

import Image from "next/image";
import { useState } from "react";
import {
  Bookmark,
  CheckCircle2,
  Clock,
  Crosshair,
  MapPin,
  Route as RouteIcon,
  ShieldCheck,
  Star,
} from "lucide-react";
import type { Experience } from "@/types/experience";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { MapSurface } from "@/components/common/MapSurface";
import { DemoDataBadge } from "@/components/ui/DemoDataBadge";
import { FeedbackControls } from "@/components/experience/FeedbackControls";
import { PersonalizationBadge } from "@/components/ui/PersonalizationBadge";
import { useUserLocation } from "@/hooks/useUserLocation";
import { getRoute } from "@/lib/api/location";
import { haversineKm } from "@/lib/geo/haversine";
import { experiencesToFeatureCollection } from "@/lib/geo/geojson";
import { ApiError } from "@/lib/api/client";
import type { RouteResponse } from "@/types/location";

export function ExperienceDetail({ experience }: { experience: Experience }) {
  const { status: geoStatus, coordinate: origin, request: requestLocation } = useUserLocation();
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [routeStatus, setRouteStatus] = useState<"idle" | "loading" | "error">("idle");

  const distanceKm = origin
    ? Math.round(haversineKm(origin.lat, origin.lng, experience.location.lat, experience.location.lng) * 10) / 10
    : null;

  async function handleShowRoute() {
    if (!origin) return;
    setRouteStatus("loading");
    try {
      const result = await getRoute(
        origin,
        { lat: experience.location.lat, lng: experience.location.lng },
        { includeGeometry: true },
      );
      setRoute(result);
      setRouteStatus("idle");
    } catch (error) {
      setRouteStatus("error");
      if (!(error instanceof ApiError)) throw error;
    }
  }

  const mapFeatures = experiencesToFeatureCollection([experience], experience.id);

  return (
    <div className="space-y-8">
      <div className="relative aspect-[16/9] w-full overflow-hidden rounded-2xl bg-surface-sunken sm:aspect-[21/9]">
        <Image
          src={experience.imageUrl}
          alt=""
          fill
          priority
          sizes="(min-width: 1024px) 1024px, 100vw"
          className="object-cover"
        />
        {experience.isSynthetic ? (
          <div className="absolute left-4 top-4">
            <DemoDataBadge label="Demo experience" />
          </div>
        ) : null}
      </div>

      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="accent">{experience.categoryLabel}</Badge>
              <Badge tone={experience.provider.verified ? "success" : "neutral"}>
                {experience.provider.verified ? (
                  <>
                    <ShieldCheck className="size-3" aria-hidden="true" /> Verified provider
                  </>
                ) : (
                  "Unverified provider"
                )}
              </Badge>
            </div>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
              {experience.title}
            </h1>
            <div className="mt-1 flex flex-wrap items-center justify-between gap-4">
              <p className="text-sm text-ink-muted">by {experience.provider.name}</p>
              <FeedbackControls experienceId={experience.id} />
            </div>
            {experience.matchSignals && experience.matchSignals.length > 0 ? (
              <div className="mt-3">
                <PersonalizationBadge signals={experience.matchSignals} />
              </div>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-muted">
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="size-4" aria-hidden="true" />
              {experience.location.area}, {experience.location.city}
              {distanceKm != null ? ` · ${distanceKm} km away` : ""}
            </span>
            {experience.durationMinutes != null ? (
              <span className="inline-flex items-center gap-1.5">
                <Clock className="size-4" aria-hidden="true" />
                {experience.durationMinutes} minutes
              </span>
            ) : null}
            <span className="inline-flex items-center gap-1.5">
              <Star className="size-4 fill-highlight text-highlight" aria-hidden="true" />
              {experience.rating != null
                ? `${experience.rating} (${experience.reviewCount ?? 0} reviews)`
                : "No ratings yet"}
            </span>
          </div>

          <div className="space-y-2">
            <h2 className="text-base font-semibold text-ink">About this experience</h2>
            <p className="text-sm leading-relaxed text-ink-muted">{experience.description}</p>
          </div>

          {experience.highlights.length > 0 ? (
            <div className="space-y-2">
              <h2 className="text-base font-semibold text-ink">Highlights</h2>
              <ul className="grid gap-1.5 sm:grid-cols-2">
                {experience.highlights.map((highlight) => (
                  <li key={highlight} className="flex items-start gap-2 text-sm text-ink-muted">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" />
                    {highlight}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="space-y-2">
            <h2 className="text-base font-semibold text-ink">Accessibility</h2>
            <p className="text-sm text-ink-muted">
              {experience.accessibility.wheelchairAccessible === null
                ? "Accessibility information is not available for this listing yet."
                : `${
                    experience.accessibility.wheelchairAccessible
                      ? "Wheelchair accessible."
                      : "Not wheelchair accessible."
                  } ${
                    experience.accessibility.stepFree
                      ? "Step-free route available."
                      : "Includes steps or uneven ground."
                  }`}
              {experience.accessibility.notes ? ` ${experience.accessibility.notes}.` : ""}
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-base font-semibold text-ink">Location &amp; travel</h2>
              {!origin ? (
                <Button variant="outline" size="sm" onClick={requestLocation} loading={geoStatus === "loading"}>
                  <Crosshair className="size-4" aria-hidden="true" />
                  Set a starting point
                </Button>
              ) : (
                <Button variant="outline" size="sm" onClick={handleShowRoute} loading={routeStatus === "loading"}>
                  <RouteIcon className="size-4" aria-hidden="true" />
                  Show route
                </Button>
              )}
            </div>
            {!origin ? (
              <p className="text-xs text-ink-subtle">Set a starting point to see travel time.</p>
            ) : route ? (
              <p className="text-xs text-ink-muted">
                {route.distance_km} km · about {Math.round(route.duration_minutes)} min by road
                {route.source === "haversine_estimate" ? " (estimated — routing unavailable)" : ""}
              </p>
            ) : routeStatus === "error" ? (
              <p className="text-xs text-danger">Travel time unavailable right now.</p>
            ) : null}
            <MapSurface
              label={`Map of ${experience.location.area}`}
              features={mapFeatures}
              origin={origin}
              routeGeometry={route?.geometry ?? null}
              center={{ lat: experience.location.lat, lng: experience.location.lng }}
              zoom={14}
            />
          </div>
        </div>

        <div className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <Card>
            <CardBody className="space-y-4">
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-semibold text-ink">
                  {experience.priceInr === 0 ? "Free" : `₹${experience.priceInr}`}
                </span>
                <span className="text-sm text-ink-subtle">
                  {experience.isPriceEstimated ? "estimated · per person" : "per person"}
                </span>
              </div>

              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-ink-subtle">Opening hours</dt>
                  <dd className="text-ink">{experience.openingHours ?? "Not available"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-subtle">Availability</dt>
                  <dd className="text-ink capitalize">{experience.availability}</dd>
                </div>
              </dl>

              <div className="space-y-2">
                <Button className="w-full" disabled title="Booking arrives in a later phase">
                  Request to book
                </Button>
                <Button variant="outline" className="w-full">
                  <Bookmark className="size-4" aria-hidden="true" />
                  Save for later
                </Button>
                <p className="text-center text-xs text-ink-subtle">
                  Booking is not yet available &mdash; this is a UI preview.
                </p>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
