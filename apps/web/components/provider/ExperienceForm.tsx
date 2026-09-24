"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { listCategories, type ApiCategory } from "@/lib/api/categories";
import { useLocationSearch } from "@/hooks/useLocationSearch";
import type { ExperienceCreateInput, ExperienceUpdateInput, OpeningHourInput } from "@/types/provider-api";

const DAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const SUITABILITY_OPTIONS = ["solo", "couple", "friends", "family", "business"];

export interface ExperienceFormValues {
  title: string;
  short_description: string;
  full_description: string;
  category_id: string;
  price: string;
  duration_minutes: string;
  minimum_group_size: string;
  maximum_group_size: string;
  capacity: string;
  wheelchair_accessible: boolean;
  step_free: boolean;
  accessibility_notes: string;
  tags: string;
  suitability: string[];
  status: "active" | "draft" | "inactive";
  openingHours: OpeningHourInput[];
  // location — create mode only
  latitude: string;
  longitude: string;
  place_name: string;
  address: string;
  locality: string;
  city: string;
}

export const EMPTY_OPENING_HOURS: OpeningHourInput[] = DAY_LABELS.map((_, day) => ({
  day_of_week: day,
  open_time: "10:00",
  close_time: "18:00",
  is_closed: day === 6,
}));

export const EMPTY_FORM_VALUES: ExperienceFormValues = {
  title: "",
  short_description: "",
  full_description: "",
  category_id: "",
  price: "",
  duration_minutes: "",
  minimum_group_size: "",
  maximum_group_size: "",
  capacity: "",
  wheelchair_accessible: false,
  step_free: false,
  accessibility_notes: "",
  tags: "",
  suitability: [],
  status: "draft",
  openingHours: EMPTY_OPENING_HOURS,
  latitude: "",
  longitude: "",
  place_name: "",
  address: "",
  locality: "",
  city: "Mumbai",
};

function toNullableNumber(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function buildCreatePayload(values: ExperienceFormValues): ExperienceCreateInput {
  return {
    title: values.title,
    short_description: values.short_description,
    full_description: values.full_description,
    category_id: values.category_id,
    location: {
      latitude: Number(values.latitude),
      longitude: Number(values.longitude),
      place_name: values.place_name || undefined,
      address: values.address || undefined,
      locality: values.locality || undefined,
      city: values.city || "Mumbai",
    },
    price: toNullableNumber(values.price),
    price_type: values.price ? "fixed" : "unknown",
    duration_minutes: toNullableNumber(values.duration_minutes),
    minimum_group_size: toNullableNumber(values.minimum_group_size),
    maximum_group_size: toNullableNumber(values.maximum_group_size),
    capacity: toNullableNumber(values.capacity),
    wheelchair_accessible: values.wheelchair_accessible,
    step_free: values.step_free,
    accessibility_notes: values.accessibility_notes || undefined,
    tags: values.tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean),
    suitability: values.suitability,
    status: values.status,
    opening_hours: values.openingHours,
  };
}

export function buildUpdatePayload(values: ExperienceFormValues): ExperienceUpdateInput {
  const payload = buildCreatePayload(values) as ExperienceUpdateInput & { location?: unknown };
  delete payload.location;
  return payload;
}

export function ExperienceForm({
  mode,
  initialValues,
  onSubmit,
  submitLabel,
  isSubmitting,
  error,
}: {
  mode: "create" | "edit";
  initialValues: ExperienceFormValues;
  onSubmit: (values: ExperienceFormValues) => void | Promise<void>;
  submitLabel: string;
  isSubmitting: boolean;
  error?: string | null;
}) {
  const [values, setValues] = useState(initialValues);
  const [categories, setCategories] = useState<ApiCategory[]>([]);
  const [placeQuery, setPlaceQuery] = useState("");
  const { status: placeSearchStatus, results: placeResults, search: searchPlace, clear: clearPlaceResults } = useLocationSearch();

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch(() => setCategories([]));
  }, []);

  function update<K extends keyof ExperienceFormValues>(key: K, value: ExperienceFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handlePlaceSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!placeQuery.trim()) return;
    await searchPlace(placeQuery);
  }

  function handlePickPlace(result: { lat: number; lng: number; display_name: string; city: string | null; locality: string | null }) {
    // Only ever applied on an explicit pick — never silently overwrites
    // a manually entered location (docs/DECISIONS.md ADR-022).
    setValues((prev) => ({
      ...prev,
      latitude: String(result.lat),
      longitude: String(result.lng),
      address: result.display_name,
      city: result.city ?? prev.city,
      locality: result.locality ?? prev.locality,
    }));
    clearPlaceResults();
    setPlaceQuery("");
  }

  function updateOpeningHour(day: number, patch: Partial<OpeningHourInput>) {
    setValues((prev) => ({
      ...prev,
      openingHours: prev.openingHours.map((window) =>
        window.day_of_week === day ? { ...window, ...patch } : window,
      ),
    }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <section className="space-y-4">
        <h2 className="text-base font-semibold text-ink">Basic details</h2>
        <Input
          label="Title"
          required
          minLength={3}
          value={values.title}
          onChange={(e) => update("title", e.target.value)}
        />
        <Textarea
          label="Short description"
          required
          minLength={10}
          maxLength={300}
          value={values.short_description}
          onChange={(e) => update("short_description", e.target.value)}
        />
        <Textarea
          label="Full description"
          required
          minLength={10}
          value={values.full_description}
          onChange={(e) => update("full_description", e.target.value)}
        />
        <label className="flex flex-col gap-1.5 text-sm font-medium text-ink">
          Category
          <select
            required
            value={values.category_id}
            onChange={(e) => update("category_id", e.target.value)}
            className="h-11 rounded-lg border border-line-strong bg-surface px-3.5 text-sm text-ink"
          >
            <option value="" disabled>
              Select a category
            </option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
      </section>

      {mode === "create" ? (
        <section className="space-y-4">
          <h2 className="text-base font-semibold text-ink">Location</h2>
          <div className="space-y-2">
            <form onSubmit={handlePlaceSearch} className="flex items-center gap-1.5">
              <input
                type="text"
                value={placeQuery}
                onChange={(e) => setPlaceQuery(e.target.value)}
                placeholder="Search a place to fill the fields below"
                className="h-9 w-72 max-w-full rounded-lg border border-line-strong bg-surface px-3 text-sm text-ink placeholder:text-ink-subtle focus:outline-none"
              />
              <Button type="submit" size="sm" variant="outline" loading={placeSearchStatus === "loading"}>
                <Search className="size-4" aria-hidden="true" />
                Search
              </Button>
            </form>
            {placeSearchStatus === "success" && placeResults.length > 0 ? (
              <ul className="max-w-md rounded-lg border border-line bg-surface p-1 shadow-sm">
                {placeResults.map((result) => (
                  <li key={`${result.lat}-${result.lng}`}>
                    <button
                      type="button"
                      onClick={() => handlePickPlace(result)}
                      className="block w-full truncate rounded-md px-3 py-2 text-left text-sm text-ink hover:bg-surface-sunken"
                    >
                      {result.display_name}
                    </button>
                  </li>
                ))}
              </ul>
            ) : placeSearchStatus === "success" ? (
              <p className="text-xs text-ink-subtle">No matching places found — enter coordinates manually below.</p>
            ) : null}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Latitude"
              type="number"
              step="any"
              required
              value={values.latitude}
              onChange={(e) => update("latitude", e.target.value)}
            />
            <Input
              label="Longitude"
              type="number"
              step="any"
              required
              value={values.longitude}
              onChange={(e) => update("longitude", e.target.value)}
            />
            <Input
              label="Place name"
              value={values.place_name}
              onChange={(e) => update("place_name", e.target.value)}
            />
            <Input label="City" value={values.city} onChange={(e) => update("city", e.target.value)} />
            <Input
              label="Address"
              className="sm:col-span-2"
              value={values.address}
              onChange={(e) => update("address", e.target.value)}
            />
            <Input
              label="Locality / area"
              value={values.locality}
              onChange={(e) => update("locality", e.target.value)}
            />
          </div>
        </section>
      ) : null}

      <section className="space-y-4">
        <h2 className="text-base font-semibold text-ink">Pricing &amp; logistics</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Price (₹)"
            type="number"
            min={0}
            value={values.price}
            onChange={(e) => update("price", e.target.value)}
          />
          <Input
            label="Duration (minutes)"
            type="number"
            min={1}
            value={values.duration_minutes}
            onChange={(e) => update("duration_minutes", e.target.value)}
          />
          <Input
            label="Minimum group size"
            type="number"
            min={1}
            value={values.minimum_group_size}
            onChange={(e) => update("minimum_group_size", e.target.value)}
          />
          <Input
            label="Maximum group size"
            type="number"
            min={1}
            value={values.maximum_group_size}
            onChange={(e) => update("maximum_group_size", e.target.value)}
          />
          <Input
            label="Capacity"
            type="number"
            min={1}
            value={values.capacity}
            onChange={(e) => update("capacity", e.target.value)}
          />
          <label className="flex flex-col gap-1.5 text-sm font-medium text-ink">
            Status
            <select
              value={values.status}
              onChange={(e) => update("status", e.target.value as ExperienceFormValues["status"])}
              className="h-11 rounded-lg border border-line-strong bg-surface px-3.5 text-sm text-ink"
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </label>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-base font-semibold text-ink">Discovery &amp; accessibility</h2>
        <Input
          label="Tags (comma-separated)"
          value={values.tags}
          onChange={(e) => update("tags", e.target.value)}
        />
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-ink">Suitable for</legend>
          <div className="flex flex-wrap gap-2">
            {SUITABILITY_OPTIONS.map((option) => (
              <label
                key={option}
                className="inline-flex items-center gap-1.5 rounded-full border border-line-strong px-3 py-1.5 text-xs capitalize text-ink-muted"
              >
                <input
                  type="checkbox"
                  checked={values.suitability.includes(option)}
                  onChange={(e) =>
                    update(
                      "suitability",
                      e.target.checked
                        ? [...values.suitability, option]
                        : values.suitability.filter((s) => s !== option),
                    )
                  }
                />
                {option}
              </label>
            ))}
          </div>
        </fieldset>
        <div className="flex flex-wrap gap-4">
          <label className="inline-flex items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              checked={values.wheelchair_accessible}
              onChange={(e) => update("wheelchair_accessible", e.target.checked)}
            />
            Wheelchair accessible
          </label>
          <label className="inline-flex items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              checked={values.step_free}
              onChange={(e) => update("step_free", e.target.checked)}
            />
            Step-free route
          </label>
        </div>
        <Textarea
          label="Accessibility notes (optional)"
          value={values.accessibility_notes}
          onChange={(e) => update("accessibility_notes", e.target.value)}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold text-ink">Opening hours</h2>
        <div className="space-y-2">
          {values.openingHours.map((window) => (
            <div key={window.day_of_week} className="flex flex-wrap items-center gap-3 text-sm">
              <span className="w-24 text-ink-muted">{DAY_LABELS[window.day_of_week]}</span>
              <label className="inline-flex items-center gap-1.5 text-xs text-ink-muted">
                <input
                  type="checkbox"
                  checked={window.is_closed}
                  onChange={(e) => updateOpeningHour(window.day_of_week, { is_closed: e.target.checked })}
                />
                Closed
              </label>
              {!window.is_closed ? (
                <>
                  <input
                    type="time"
                    value={window.open_time ?? "10:00"}
                    onChange={(e) => updateOpeningHour(window.day_of_week, { open_time: e.target.value })}
                    className="h-9 rounded-md border border-line-strong bg-surface px-2 text-sm text-ink"
                  />
                  <span className="text-ink-subtle">to</span>
                  <input
                    type="time"
                    value={window.close_time ?? "18:00"}
                    onChange={(e) => updateOpeningHour(window.day_of_week, { close_time: e.target.value })}
                    className="h-9 rounded-md border border-line-strong bg-surface px-2 text-sm text-ink"
                  />
                </>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}

      <Button type="submit" loading={isSubmitting}>
        {submitLabel}
      </Button>
    </form>
  );
}
