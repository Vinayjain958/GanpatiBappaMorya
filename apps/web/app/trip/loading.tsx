import { PageContainer } from "@/components/layout/PageContainer";
import { Skeleton } from "@/components/ui/Skeleton";

export default function TripLoading() {
  return (
    <PageContainer className="space-y-6 py-8" aria-busy="true" aria-live="polite">
      <Skeleton className="h-8 w-56" />
      <Skeleton className="h-24 w-full rounded-xl" />
      <Skeleton className="h-24 w-full rounded-xl" />
    </PageContainer>
  );
}
