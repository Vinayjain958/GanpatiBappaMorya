import { PageContainer } from "@/components/layout/PageContainer";
import { Skeleton } from "@/components/ui/Skeleton";

export default function ExperienceDetailLoading() {
  return (
    <PageContainer className="space-y-8 py-8" aria-busy="true" aria-live="polite">
      <Skeleton className="aspect-[16/9] w-full rounded-2xl sm:aspect-[21/9]" />
      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-4">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-24 w-full" />
        </div>
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    </PageContainer>
  );
}
