import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, MapPin, PhoneCall, ShieldAlert } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";

export const metadata: Metadata = { title: "Emergency" };

const localNumbers = [
  { label: "Police", number: "100" },
  { label: "Ambulance", number: "102" },
  { label: "Fire", number: "101" },
  { label: "Women's helpline", number: "1091" },
];

export default function EmergencyPage() {
  return (
    <PageContainer className="max-w-2xl space-y-6 py-8">
      <Link href="/safety" className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink">
        <ArrowLeft className="size-4" aria-hidden="true" />
        Back to Safety Center
      </Link>

      <div className="rounded-xl border border-danger/30 bg-danger-soft p-5">
        <h1 className="flex items-center gap-2 text-xl font-semibold text-ink">
          <ShieldAlert className="size-6 text-danger" aria-hidden="true" />
          Emergency
        </h1>
        <p className="mt-1 text-sm text-ink-muted">
          If you are in immediate danger, call local emergency services directly. Live emergency
          integrations are not implemented yet in this build.
        </p>
      </div>

      <Card>
        <CardBody className="space-y-3">
          <h2 className="text-sm font-semibold text-ink">Local emergency numbers</h2>
          <ul className="divide-y divide-line">
            {localNumbers.map((entry) => (
              <li key={entry.label} className="flex items-center justify-between py-2.5">
                <span className="text-sm text-ink-muted">{entry.label}</span>
                <a href={`tel:${entry.number}`} className="inline-flex items-center gap-1.5 font-semibold text-ink">
                  <PhoneCall className="size-4" aria-hidden="true" />
                  {entry.number}
                </a>
              </li>
            ))}
          </ul>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="space-y-3">
          <h2 className="flex items-center gap-1.5 text-sm font-semibold text-ink">
            <MapPin className="size-4" aria-hidden="true" />
            Your location
          </h2>
          <p className="text-sm text-ink-muted">
            Location sharing with emergency contacts is not yet implemented.
          </p>
          <Button variant="outline" disabled title="Not yet implemented">
            Share my location
          </Button>
        </CardBody>
      </Card>
    </PageContainer>
  );
}
