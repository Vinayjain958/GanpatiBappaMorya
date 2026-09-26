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
      className="flex gap-2 overflow-x-auto pb-1 scrollbar-none"
    >
      <button
        type="button"
        aria-pressed={value === null}
        onClick={() => onChange(null)}
        className={cn(
          "shrink-0 rounded-full border px-3.5 py-2 text-sm font-medium transition-colors",
          value === null
            ? "border-transparent bg-pastel-lemon text-ink"
            : "border-line bg-surface text-ink-muted hover:border-line-strong hover:bg-pastel-lavender/35 hover:text-ink",
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
            "shrink-0 rounded-full border px-3.5 py-2 text-sm font-medium transition-colors",
            value === option.value
              ? "border-transparent bg-pastel-lemon text-ink"
              : "border-line bg-surface text-ink-muted hover:border-line-strong hover:bg-pastel-lavender/35 hover:text-ink",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}