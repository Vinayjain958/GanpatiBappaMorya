"use client";

import { GENDER_OPTIONS, MAX_PARTICIPANT_AGE, MIN_PARTICIPANT_AGE } from "@/lib/trip/planningForm";
import type { ParticipantDraft } from "@/lib/trip/planningForm";
import type { ParticipantGender } from "@/types/api";

/**
 * One row per traveler ("Traveler 1", "Traveler 2", ...). Rows are created
 * and trimmed by resizeParticipants() in lib/trip/planningForm.ts — this
 * component only renders them. No names are collected (data minimization).
 */
export function ParticipantFields({
  participants,
  errors,
  disabled,
  controlClassName,
  onChange,
}: {
  participants: ParticipantDraft[];
  errors: Record<number, string>;
  disabled: boolean;
  controlClassName: string;
  onChange: (sequence: number, patch: Partial<Pick<ParticipantDraft, "age" | "gender">>) => void;
}) {
  return (
    <div className="space-y-2">
      {participants.map((participant) => {
        const error = errors[participant.sequence];
        const errorId = `participant-${participant.sequence}-error`;
        return (
          <fieldset
            key={participant.sequence}
            className="rounded-xl border border-line bg-surface px-3 py-2.5"
            disabled={disabled}
          >
            <legend className="px-1 text-xs font-semibold text-ink">Traveler {participant.sequence}</legend>
            <div className="grid grid-cols-2 gap-2">
              <label className="block text-xs">
                <span className="mb-1 block text-ink-muted">Age</span>
                <input
                  type="number"
                  inputMode="numeric"
                  min={MIN_PARTICIPANT_AGE}
                  max={MAX_PARTICIPANT_AGE}
                  step={1}
                  className={controlClassName}
                  value={participant.age}
                  onChange={(event) => onChange(participant.sequence, { age: event.target.value })}
                  aria-invalid={Boolean(error)}
                  aria-describedby={error ? errorId : undefined}
                  required
                />
              </label>
              <label className="block text-xs">
                <span className="mb-1 block text-ink-muted">Gender (optional)</span>
                <select
                  className={controlClassName}
                  value={participant.gender}
                  onChange={(event) =>
                    onChange(participant.sequence, { gender: event.target.value as ParticipantGender | "" })
                  }
                >
                  <option value="">Not specified</option>
                  {GENDER_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {error ? (
              <p id={errorId} className="mt-1.5 text-xs text-danger">
                {error}
              </p>
            ) : null}
          </fieldset>
        );
      })}
    </div>
  );
}
