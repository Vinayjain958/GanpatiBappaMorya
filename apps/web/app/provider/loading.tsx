import { PageContainer } from "@/components/layout/PageContainer";
import { Skeleton } from "@/components/ui/Skeleton";

export default function ProviderLoading() {
  return (
    <PageContainer className="space-y-6 py-8" aria-busy="true" aria-live="polite">
      <Skeleton className="h-8 w-64" />
      <div className="grid gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-24 w-full rounded-xl" />
        ))}
      </div>
    </PageContainer>
  );
}
