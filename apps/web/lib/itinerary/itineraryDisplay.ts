import type { ApiItinerary, ApiItineraryItem, BookingStatus } from "@/types/api";

/**
 * Pure, deterministic display helpers for itinerary/booking data (Phase
 * 8) — no business logic in React components (same convention as
 * lib/feasibility/feasibilityDisplay.ts). The frontend never reorders
 * `items`; these helpers only format/derive display text from the
 * backend's own ordering.
 *
 * Hard invariant: REQUESTED and ACCEPTED booking statuses are never
 * displayed as "Confirmed" — see docs/DECISIONS.md ADR-046.
 */

const BOOKING_STATUS_LABELS: Record<BookingStatus, string> = {
  REQUESTED: "Requested",
  ACCEPTED: "Accepted",
  DECLINED: "Declined",
  CANCELLED: "Cancelled",
  EXPIRED: "Expired",
};

export function bookingStatusLabel(status: BookingStatus): string {
  return BOOKING_STATUS_LABELS[status] ?? status;
}

export type BookingStatusTone = "success" | "warning" | "danger" | "neutral";

const BOOKING_STATUS_TONES: Record<BookingStatus, BookingStatusTone> = {
  REQUESTED: "warning",
  ACCEPTED: "success",
  DECLINED: "danger",
  CANCELLED: "neutral",
  EXPIRED: "neutral",
};

export function bookingStatusTone(status: BookingStatus): BookingStatusTone {
  return BOOKING_STATUS_TONES[status] ?? "neutral";
}

/** Formats a travel gap for display — never assumes 0 minutes when the
 * backend reports the transition as unknown (null). */
export function travelGapLabel(item: ApiItineraryItem): string | null {
  if (item.travel_from_previous_minutes == null) {
    if (item.sequence_order === 1) return null; // first stop: no previous gap
    return "Travel time unknown";
  }
  const minutes = Math.round(item.travel_from_previous_minutes);
  if (minutes <= 0) return null;
  return `${minutes} min travel`;
}

export function formatItemTimeRange(item: ApiItineraryItem): string {
  const start = new Date(item.planned_start);
  const end = new Date(item.planned_end);
  const fmt = (d: Date) =>
    d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
  return `${fmt(start)}–${fmt(end)}`;
}

export function formatCost(cost: number | null, currency: string): string {
  if (cost == null) return "Price unavailable";
  if (cost === 0) return "Free";
  return `${currency === "INR" ? "₹" : currency + " "}${cost}`;
}

/** Renders items in EXACTLY the order the backend returned them —
 * callers must never sort/reorder this array themselves. */
export function orderedItems(itinerary: ApiItinerary): ApiItineraryItem[] {
  return itinerary.items;
}

export function itinerarySummaryLine(itinerary: ApiItinerary): string {
  const count = itinerary.items.length;
  const stops = `${count} stop${count === 1 ? "" : "s"}`;
  const cost =
    itinerary.estimated_total_cost != null
      ? formatCost(itinerary.estimated_total_cost, itinerary.currency)
      : null;
  return cost ? `${stops} · ${cost}` : stops;
}

const ITINERARY_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  VALIDATED: "Ready",
  BOOKING_REQUESTED: "Booking requested",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
};

export function itineraryStatusLabel(status: string): string {
  return ITINERARY_STATUS_LABELS[status] ?? status;
}
