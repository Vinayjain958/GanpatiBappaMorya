"use client";

import { categoryOptions } from "@/lib/constants/categories";
import { cn } from "@/lib/utils/cn";

export function CategoryChips({
  value,
  onChange,
}: {
  value: string | null;
  onChange: (value: string | null) => void;
}) {
  return (
    <div
      role="group"
      aria-label="Filter by category"
      className="flex gap-2 overflow-x-auto scrollbar-none pb-1"
    >
      <button
        type="button"
        aria-pressed={value === null}
        onClick={() => onChange(null)}
        className={cn(
          "shrink-0 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
          value === null
            ? "border-primary bg-primary text-primary-ink"
            : "border-line-strong text-ink-muted hover:text-ink",
        )}
      >
        All
      </button>
      {categoryOptions.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "shrink-0 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
            value === option.value
              ? "border-primary bg-primary text-primary-ink"
              : "border-line-strong text-ink-muted hover:text-ink",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
