"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { CalendarClock, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardBody } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  createAvailability,
  deactivateAvailability,
  listAvailability,
} from "@/lib/api/experiencesWrite";
import type { AvailabilitySlot } from "@/types/provider-api";
import { ApiError } from "@/lib/api/client";

function formatSlot(slot: AvailabilitySlot): string {
  const start = new Date(slot.starts_at);
  const end = new Date(slot.ends_at);
  return `${start.toLocaleDateString()} · ${start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}–${end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

export function AvailabilityManager({ experienceId }: { experienceId: string }) {
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [reloadToken, setReloadToken] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [starts, setStarts] = useState("");
  const [ends, setEnds] = useState("");
  const [capacity, setCapacity] = useState("8");

  useEffect(() => {
    let cancelled = false;
    listAvailability(experienceId)
      .then((data) => {
        if (!cancelled) {
          setSlots(data);
          setStatus("success");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [experienceId, reloadToken]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setIsCreating(true);
    try {
      await createAvailability(experienceId, {
        starts_at: new Date(starts).toISOString(),
        ends_at: new Date(ends).toISOString(),
        capacity: Number(capacity),
      });
      setStarts("");
      setEnds("");
      setReloadToken((t) => t + 1);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Couldn't add that slot.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDeactivate(id: string) {
    await deactivateAvailability(experienceId, id);
    setReloadToken((t) => t + 1);
  }

  return (
    <Card>
      <CardBody className="space-y-4">
        <div className="flex items-center gap-2">
          <CalendarClock className="size-4 text-accent" aria-hidden="true" />
          <h2 className="text-base font-semibold text-ink">Availability</h2>
        </div>

        <form onSubmit={handleCreate} className="grid gap-3 sm:grid-cols-4 sm:items-end">
          <Input
            label="Starts"
            type="datetime-local"
            required
            value={starts}
            onChange={(e) => setStarts(e.target.value)}
          />
          <Input
            label="Ends"
            type="datetime-local"
            required
            value={ends}
            onChange={(e) => setEnds(e.target.value)}
          />
          <Input
            label="Capacity"
            type="number"
            min={1}
            required
            value={capacity}
            onChange={(e) => setCapacity(e.target.value)}
          />
          <Button type="submit" size="sm" loading={isCreating}>
            <Plus className="size-4" aria-hidden="true" />
            Add slot
          </Button>
        </form>
        {formError ? (
          <p role="alert" className="text-xs text-danger">
            {formError}
          </p>
        ) : null}

        {status === "loading" ? (
          <div className="space-y-2" aria-busy="true">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : status === "error" ? (
          <p className="text-sm text-danger">Couldn&apos;t load availability slots.</p>
        ) : slots.length === 0 ? (
          <EmptyState icon={CalendarClock} title="No availability yet" description="Add a slot above." />
        ) : (
          <ul className="space-y-2">
            {slots.map((slot) => (
              <li
                key={slot.id}
                className="flex items-center justify-between rounded-lg border border-line px-3 py-2 text-sm"
              >
                <div>
                  <p className="text-ink">{formatSlot(slot)}</p>
                  <p className="text-xs text-ink-subtle">
                    Capacity {slot.capacity} · {slot.status}
                  </p>
                </div>
                {slot.status === "active" ? (
                  <Button variant="ghost" size="sm" onClick={() => handleDeactivate(slot.id)}>
                    <Trash2 className="size-4" aria-hidden="true" />
                  </Button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
