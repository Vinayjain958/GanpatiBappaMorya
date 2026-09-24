import { forwardRef } from "react";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  active?: boolean;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, label, active, children, ...props }, ref) => (
    <button
      ref={ref}
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex size-10 items-center justify-center rounded-lg border border-line-strong text-ink-muted transition-colors",
        "hover:bg-surface-sunken hover:text-ink",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        active && "border-accent text-accent bg-accent-soft",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  ),
);
IconButton.displayName = "IconButton";
