import { PageContainer } from "@/components/layout/PageContainer";
import { Skeleton } from "@/components/ui/Skeleton";

export default function DiscoverLoading() {
  return (
    <PageContainer className="space-y-6 py-8" aria-busy="true" aria-live="polite">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-14 w-full rounded-2xl" />
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-72 w-full rounded-xl" />
        ))}
      </div>
    </PageContainer>
  );
}
