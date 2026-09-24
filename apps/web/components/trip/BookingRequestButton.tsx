"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";
import { createBookingRequest } from "@/lib/api/bookings";
import { bookingStatusLabel, bookingStatusTone } from "@/lib/itinerary/itineraryDisplay";
import type { ApiBookingRequest, BookingStatus } from "@/types/api";

/**
 * Request/Requested/Accepted/Declined/Cancelled state button. Never
 * shows "Confirmed" for a REQUESTED (or even ACCEPTED) status — REQUESTED
 * intent only, no payment, ever (docs/DECISIONS.md ADR-046).
 */
export function BookingRequestButton({
  itineraryId,
  itineraryItemId,
  initialBooking,
}: {
  itineraryId: string;
  itineraryItemId: string;
  initialBooking?: ApiBookingRequest | null;
}) {
  const [booking, setBooking] = useState<ApiBookingRequest | null>(initialBooking ?? null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (booking) {
    const tone = bookingStatusTone(booking.status as BookingStatus);
    return (
      <Badge tone={tone === "neutral" ? "neutral" : tone}>{bookingStatusLabel(booking.status as BookingStatus)}</Badge>
    );
  }

  async function handleRequest() {
    setSubmitting(true);
    setError(null);
    try {
      const created = await createBookingRequest(itineraryId, { itinerary_item_id: itineraryItemId });
      setBooking(created);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send the booking request.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button size="sm" variant="outline" loading={submitting} onClick={handleRequest}>
        Request booking
      </Button>
      {error ? <span className="text-xs text-danger">{error}</span> : null}
    </div>
  );
}
