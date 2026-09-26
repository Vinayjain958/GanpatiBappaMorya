"use client";

import { useState, useCallback } from "react";
import { Bookmark } from "lucide-react";
import { feedbackApi } from "@/lib/api/feedback";
import { InteractionEventType } from "@/types/api";
import { cn } from "@/lib/utils/cn";

export interface FeedbackControlsProps {
  experienceId: string;
  initialSaved?: boolean;
  onSaveToggle?: (saved: boolean) => void;
  className?: string;
}

export function FeedbackControls({
  experienceId,
  initialSaved = false,
  onSaveToggle,
  className,
}: FeedbackControlsProps) {
  const [isSaved, setIsSaved] = useState(initialSaved);

  const recordInteraction = useCallback(
    async (eventType: InteractionEventType) => {
      try {
        await feedbackApi.recordInteraction({
          experience_id: experienceId,
          event_type: eventType,
          client_event_id: `${experienceId}-${eventType}-${Date.now()}`,
        });
      } catch (err) {
        console.error("Failed to record interaction:", err);
      }
    },
    [experienceId],
  );

  const handleSaveToggle = () => {
    const newState = !isSaved;
    setIsSaved(newState);
    onSaveToggle?.(newState);
    recordInteraction(newState ? "SAVE" : "UNSAVE");
  };

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <button
        type="button"
        onClick={(event) => {
          event.preventDefault();
          handleSaveToggle();
        }}
        aria-pressed={isSaved}
        className={cn(
          "inline-flex h-10 items-center justify-center gap-2 rounded-full border px-4 text-sm font-medium transition-colors",
          "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
          isSaved
            ? "border-accent/25 bg-accent-soft text-accent"
            : "border-line bg-surface text-ink-muted hover:bg-surface-raised hover:text-ink",
        )}
      >
        <Bookmark className={cn("size-4", isSaved && "fill-current")} aria-hidden="true" />
        {isSaved ? "Saved" : "Save"}
      </button>
    </div>
  );
}
