import type { ReactNode } from "react";
import Link from "next/link";
import { Compass } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Card, CardBody } from "@/components/ui/Card";

export function AuthCard({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <PageContainer className="flex min-h-[calc(100vh-4rem)] items-center justify-center py-12">
      <div className="w-full max-w-sm space-y-6">
        <Link href="/" className="flex items-center justify-center gap-2 font-semibold text-ink">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-ink">
            <Compass className="size-4.5" aria-hidden="true" />
          </span>
          LocaLens
        </Link>

        <Card>
          <CardBody className="space-y-5">
            <div className="space-y-1 text-center">
              <h1 className="text-xl font-semibold text-ink">{title}</h1>
              <p className="text-sm text-ink-muted">{description}</p>
            </div>
            {children}
          </CardBody>
        </Card>

        <p className="text-center text-sm text-ink-muted">{footer}</p>
      </div>
    </PageContainer>
  );
}
