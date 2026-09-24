import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { PageContainer } from "@/components/layout/PageContainer";
import { ExperienceComposer } from "@/components/experience/ExperienceComposer";
import { ItineraryTimeline } from "@/components/trip/ItineraryTimeline";
import { mockTrip } from "@/mocks/trip";

export async function generateMetadata({ params }: PageProps<"/trip/[id]">): Promise<Metadata> {
  const { id } = await params;
  return { title: id === mockTrip.id ? mockTrip.title : "Trip" };
}

export default async function TripDetailPage({ params }: PageProps<"/trip/[id]">) {
  const { id } = await params;
  if (id !== mockTrip.id) notFound();

  return (
    <PageContainer className="space-y-8 py-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">{mockTrip.title}</h1>
        <p className="text-sm text-ink-muted">{mockTrip.date}</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1fr_400px]">
        <ItineraryTimeline trip={mockTrip} />
        <div className="lg:sticky lg:top-24 lg:self-start">
          <ExperienceComposer trip={mockTrip} />
        </div>
      </div>
    </PageContainer>
  );
}
