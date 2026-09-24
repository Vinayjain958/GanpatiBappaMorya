"use client";

import { ArrowUpDown, Clock, MapPinned, Wallet } from "lucide-react";
import { budgetOptions, durationOptions } from "@/lib/constants/categories";
import type { DiscoverySort } from "@/types/api";
import type { BudgetOption, DurationOption } from "@/types/discovery";

const sortOptions: { value: DiscoverySort; label: string }[] = [
  { value: "relevance", label: "Relevance" },
  { value: "distance", label: "Nearest" },
  { value: "price", label: "Price: low to high" },
  { value: "duration", label: "Duration: shortest" },
  { value: "newest", label: "Newest" },
];

function FilterSelect<T extends string>({
  icon: Icon,
  label,
  value,
  options,
  onChange,
  disabledOptionValues,
}: {
  icon: typeof Clock;
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
  disabledOptionValues?: T[];
}) {
  return (
    <label className="inline-flex items-center gap-2 rounded-lg border border-line-strong bg-surface px-3 py-2 text-sm text-ink-muted">
      <Icon className="size-4 shrink-0" aria-hidden="true" />
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as T)}
        className="bg-transparent text-ink focus:outline-none"
        aria-label={label}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value} disabled={disabledOptionValues?.includes(option.value)}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export interface FilterBarValue {
  budget: BudgetOption;
  duration: DurationOption;
  sort: DiscoverySort;
}

export function FilterBar({
  value,
  onChange,
  hasLocation,
}: {
  value: FilterBarValue;
  onChange: (value: FilterBarValue) => void;
  hasLocation: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <FilterSelect
        icon={Wallet}
        label="Budget"
        value={value.budget}
        options={budgetOptions as { value: BudgetOption; label: string }[]}
        onChange={(budget) => onChange({ ...value, budget })}
      />
      <FilterSelect
        icon={Clock}
        label="Duration"
        value={value.duration}
        options={durationOptions as { value: DurationOption; label: string }[]}
        onChange={(duration) => onChange({ ...value, duration })}
      />
      <FilterSelect
        icon={ArrowUpDown}
        label="Sort"
        value={value.sort}
        options={sortOptions}
        onChange={(sort) => onChange({ ...value, sort })}
        disabledOptionValues={hasLocation ? [] : (["distance"] as DiscoverySort[])}
      />
      {!hasLocation ? (
        <span className="inline-flex items-center gap-1.5 text-xs text-ink-subtle">
          <MapPinned className="size-3.5" aria-hidden="true" />
          Set a location to sort by distance
        </span>
      ) : null}
    </div>
  );
}
