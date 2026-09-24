"use client";

import { useState, useCallback } from "react";
import { ThumbsUp, ThumbsDown, Bookmark } from "lucide-react";
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
  className 
}: FeedbackControlsProps) {
  const [isSaved, setIsSaved] = useState(initialSaved);
  const [rating, setRating] = useState<number | null>(null);
  const [isVoting, setIsVoting] = useState(false);

  const recordInteraction = useCallback(async (
    eventType: InteractionEventType, 
    value?: number
  ) => {
    try {
      await feedbackApi.recordInteraction({
        experience_id: experienceId,
        event_type: eventType,
        rating: value,
        client_event_id: `${experienceId}-${eventType}-${Date.now()}`
      });
    } catch (err) {
      console.error("Failed to record interaction:", err);
    }
  }, [experienceId]);

  const handleSaveToggle = () => {
    const newState = !isSaved;
    setIsSaved(newState);
    onSaveToggle?.(newState);
    recordInteraction(newState ? "SAVE" : "UNSAVE");
  };

  const handleVote = async (isPositive: boolean) => {
    if (isVoting) return;
    setIsVoting(true);
    setRating(isPositive ? 5 : 1);
    await recordInteraction("RATING", isPositive ? 5 : 1);
    setIsVoting(false);
  };

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <button
        type="button"
        onClick={(e) => {
          e.preventDefault();
          handleSaveToggle();
        }}
        aria-pressed={isSaved}
        className={cn(
          "inline-flex h-9 items-center justify-center gap-2 rounded-md border px-3 text-sm font-medium transition-colors hover:bg-surface-sunken",
          isSaved ? "border-accent text-accent bg-accent/5" : "border-line text-ink-subtle"
        )}
      >
        <Bookmark className={cn("size-4", isSaved && "fill-current")} />
        {isSaved ? "Saved" : "Save"}
      </button>

      <div className="flex h-9 items-center gap-0.5 rounded-md border border-line bg-surface px-1">
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            handleVote(true);
          }}
          disabled={isVoting || rating === 5}
          className={cn(
            "inline-flex size-7 items-center justify-center rounded-sm transition-colors hover:bg-surface-sunken hover:text-ink",
            rating === 5 ? "text-success bg-success/10" : "text-ink-subtle"
          )}
          aria-label="Thumbs up"
        >
          <ThumbsUp className={cn("size-4", rating === 5 && "fill-current")} />
        </button>
        <div className="h-4 w-px bg-line mx-0.5" />
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            handleVote(false);
          }}
          disabled={isVoting || rating === 1}
          className={cn(
            "inline-flex size-7 items-center justify-center rounded-sm transition-colors hover:bg-surface-sunken hover:text-ink",
            rating === 1 ? "text-danger bg-danger/10" : "text-ink-subtle"
          )}
          aria-label="Thumbs down"
        >
          <ThumbsDown className={cn("size-4", rating === 1 && "fill-current")} />
        </button>
      </div>
    </div>
  );
}
