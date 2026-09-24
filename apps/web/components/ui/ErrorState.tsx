import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils/cn";

export interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  description = "We couldn't load this content. Please try again.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-danger/20 bg-danger-soft px-6 py-14 text-center",
        className,
      )}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-surface text-danger">
        <AlertTriangle className="size-6" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-semibold text-ink">{title}</p>
        <p className="max-w-sm text-sm text-ink-muted">{description}</p>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}
