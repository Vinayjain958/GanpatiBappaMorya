"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Brain, Compass, MessageSquareText, Sparkles, Store, Waypoints } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { ConversationalDiscoveryInput } from "@/components/discovery/ConversationalDiscoveryInput";
import { ExperienceCard } from "@/components/experience/ExperienceCard";
import { ExperienceComposer } from "@/components/experience/ExperienceComposer";
import { ApiStatusBadge } from "@/components/common/ApiStatusBadge";
import { DemoDataBadge } from "@/components/ui/DemoDataBadge";
import { Button } from "@/components/ui/Button";
import { mockExperiences } from "@/mocks/experiences";
import { mockTrip } from "@/mocks/trip";

const loop = [
  {
    icon: MessageSquareText,
    title: "Understand",
    description: "LocaLens reads your context — time, budget, group, and what you're actually after.",
  },
  {
    icon: Compass,
    title: "Match",
    description: "It retrieves experiences that fit your context from the local catalog.",
  },
  {
    icon: Sparkles,
    title: "Compose",
    description: "Compatible experiences are assembled into a realistic, time-ordered plan.",
  },
  {
    icon: Waypoints,
    title: "Adapt",
    description: "When plans change, LocaLens re-checks feasibility and adjusts.",
  },
];

export default function LandingPage() {
  const router = useRouter();

  function handleQuery(query: string) {
    router.push(`/discover?q=${encodeURIComponent(query)}`);
  }

  return (
    <>
      <section className="relative overflow-hidden border-b border-line bg-surface">
        <div
          className="pointer-events-none absolute inset-0 opacity-70"
          style={{
            background:
              "radial-gradient(60% 50% at 50% 0%, var(--color-accent-soft), transparent 70%)",
          }}
          aria-hidden="true"
        />
        <PageContainer className="relative flex flex-col items-center gap-8 py-16 text-center sm:py-24">
          <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3.5 py-1.5 text-xs font-medium text-ink-muted">
            <Brain className="size-3.5 text-accent" aria-hidden="true" />
            AI-native local experience companion
          </span>

          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            Discover local experiences based on what you actually want
          </h1>
          <p className="max-w-xl text-base text-ink-muted sm:text-lg">
            Not just where you are. Tell LocaLens your context — it understands, matches, and will
            eventually compose the right experience for you.
          </p>

          <div className="w-full max-w-2xl">
            <ConversationalDiscoveryInput onSubmitQuery={handleQuery} />
          </div>

          <ApiStatusBadge />
        </PageContainer>
      </section>

      <section className="border-b border-line py-14 sm:py-20">
        <PageContainer>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {loop.map((step, index) => (
              <div key={step.title} className="relative rounded-xl border border-line bg-surface p-5">
                <span className="text-xs font-semibold text-ink-subtle">0{index + 1}</span>
                <span className="mt-3 flex size-10 items-center justify-center rounded-lg bg-primary text-primary-ink">
                  <step.icon className="size-5" aria-hidden="true" />
                </span>
                <h3 className="mt-3 font-semibold text-ink">{step.title}</h3>
                <p className="mt-1 text-sm text-ink-muted">{step.description}</p>
              </div>
            ))}
          </div>
        </PageContainer>
      </section>

      <section className="border-b border-line py-14 sm:py-20">
        <PageContainer>
          <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-accent">Personalized discovery</p>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight text-ink">
                Experiences that fit your moment
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <DemoDataBadge />
              <Link href="/discover">
                <Button variant="outline" size="sm">
                  Browse all
                </Button>
              </Link>
            </div>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {mockExperiences.slice(0, 3).map((experience) => (
              <ExperienceCard key={experience.id} experience={experience} />
            ))}
          </div>
        </PageContainer>
      </section>

      <section className="border-b border-line py-14 sm:py-20">
        <PageContainer className="grid gap-10 lg:grid-cols-2 lg:items-center">
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-accent">Dynamic planning</p>
            <h2 className="text-2xl font-semibold tracking-tight text-ink">
              From a request to a coherent plan
            </h2>
            <p className="text-sm text-ink-muted">
              LocaLens will eventually compose compatible experiences into a single itinerary —
              accounting for travel time, opening hours, and budget — and adapt it when your
              plans change.
            </p>
          </div>
          <ExperienceComposer trip={mockTrip} />
        </PageContainer>
      </section>

      <section className="py-14 sm:py-20">
        <PageContainer className="grid gap-6 rounded-2xl border border-line bg-surface p-8 sm:grid-cols-[1fr_auto] sm:items-center sm:p-10">
          <div className="space-y-2">
            <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-accent">
              <Store className="size-3.5" aria-hidden="true" />
              For local providers
            </p>
            <h2 className="text-2xl font-semibold tracking-tight text-ink">
              Get discovered by travelers who are a genuine fit
            </h2>
            <p className="max-w-xl text-sm text-ink-muted">
              List your experience, see who&apos;s interested, and get demand intelligence to
              improve your offering.
            </p>
          </div>
          <Link href="/provider">
            <Button size="lg">List your experience</Button>
          </Link>
        </PageContainer>
      </section>
    </>
  );
}
