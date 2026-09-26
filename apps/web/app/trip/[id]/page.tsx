import type { Metadata } from "next";
import { PageContainer } from "@/components/layout/PageContainer";
import { RequireRole } from "@/components/common/RequireRole";
import { TripDetailClient } from "@/components/trip/TripDetailClient";

export const metadata: Metadata = { title: "Trip" };

/**
 * /trip/[id] — any itinerary the signed-in traveler owns, loaded from
 * GET /api/v1/itineraries/{id} on the client (the access token lives in
 * memory, so this can't be fetched during server rendering). The backend
 * returns 404 for an id the traveler doesn't own, rendered as "not found".
 */
export default async function TripDetailPage({
  params,
}: PageProps<"/trip/[id]">) {
  const { id } = await params;

  return (
    <RequireRole role="traveler">
      <PageContainer className="space-y-6 py-6 sm:space-y-8 sm:py-8">
        <TripDetailClient itineraryId={id} />
      </PageContainer>
    </RequireRole>
  );
}
