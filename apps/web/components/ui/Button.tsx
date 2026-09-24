import { forwardRef } from "react";
import type { ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils/cn";

type Variant = "primary" | "secondary" | "outline" | "ghost" | "danger";
type Size = "sm" | "md" | "lg" | "icon";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-primary text-primary-ink hover:brightness-110 active:brightness-95 shadow-sm shadow-black/5",
  secondary:
    "bg-accent text-accent-ink hover:brightness-105 active:brightness-95 shadow-sm shadow-black/5",
  outline:
    "border border-line-strong text-ink bg-transparent hover:bg-surface-sunken",
  ghost: "text-ink hover:bg-surface-sunken",
  danger: "bg-danger text-white hover:brightness-110",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-9 px-3.5 text-sm gap-1.5 rounded-md",
  md: "h-11 px-5 text-sm gap-2 rounded-lg",
  lg: "h-13 px-6 text-base gap-2 rounded-lg",
  icon: "h-10 w-10 rounded-lg",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors duration-150",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        {...props}
      >
        {loading ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : null}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";
