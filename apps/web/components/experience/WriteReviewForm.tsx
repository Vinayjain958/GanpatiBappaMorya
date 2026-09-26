"use client";

import { useState } from "react";
import { Star } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { useAuth } from "@/lib/auth/AuthContext";
import { createExperienceReview } from "@/lib/api/experiences";
import { ApiError } from "@/lib/api/client";
import type { ExperienceRatingSummary, ReviewItem } from "@/types/experience";
import { cn } from "@/lib/utils/cn";

export interface WriteReviewFormProps {
  experienceId: string;
  onSubmitted: (review: ReviewItem, ratingSummary: ExperienceRatingSummary) => void;
}

export function WriteReviewForm({ experienceId, onSubmitted }: WriteReviewFormProps) {
  const { isAuthenticated, traveler } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!isAuthenticated || !traveler) {
    return (
      <div className="rounded-2xl border border-dashed border-line bg-surface-raised/40 p-4 text-sm text-ink-muted">
        <a href="/login" className="font-semibold text-accent hover:underline">
          Log in
        </a>{" "}
        as a traveler to write a review.
      </div>
    );
  }

  if (success) {
    return (
      <div className="rounded-2xl border border-success/30 bg-success-soft/60 p-4 text-sm text-ink">
        Thanks — your review has been posted.
      </div>
    );
  }

  if (!expanded) {
    return (
      <Button variant="outline" size="sm" onClick={() => setExpanded(true)} className="rounded-full">
        Write a review
      </Button>
    );
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (rating < 1 || rating > 5) {
      setError("Please choose a star rating.");
      return;
    }
    if (title.trim().length === 0 || body.trim().length === 0) {
      setError("Please fill in both a title and your review.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await createExperienceReview(experienceId, {
        rating_value: rating,
        title: title.trim(),
        body: body.trim(),
      });
      onSubmitted(
        {
          id: response.review.id,
          rating: response.review.rating_value,
          title: response.review.title,
          body: response.review.body,
          author: response.review.author_display_name,
          reviewedAt: response.review.reviewed_at,
          isSynthetic: response.review.is_synthetic,
        },
        {
          averageRating: response.rating_summary.average_rating ?? 0,
          reviewCount: response.rating_summary.review_count,
          distribution: Object.fromEntries(
            Object.entries(response.rating_summary.rating_distribution).map(([k, v]) => [
              parseInt(k, 10),
              v,
            ]),
          ),
          isSynthetic: response.rating_summary.is_synthetic,
        },
      );
      setSuccess(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit your review. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-2xl border border-line bg-surface-raised/40 p-4"
    >
      <div>
        <p className="mb-1.5 text-sm font-medium text-ink">Your rating</p>
        <div
          className="flex gap-1"
          onMouseLeave={() => setHoverRating(0)}
          role="radiogroup"
          aria-label="Star rating"
        >
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              role="radio"
              aria-checked={rating === star}
              aria-label={`${star} star${star === 1 ? "" : "s"}`}
              onMouseEnter={() => setHoverRating(star)}
              onClick={() => setRating(star)}
              className="p-0.5"
            >
              <Star
                className={cn(
                  "size-6 transition-colors",
                  star <= (hoverRating || rating)
                    ? "fill-highlight text-highlight"
                    : "text-line",
                )}
              />
            </button>
          ))}
        </div>
      </div>

      <Input
        label="Title"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        maxLength={160}
        placeholder="Sum up your visit"
        required
      />

      <Textarea
        label="Your review"
        value={body}
        onChange={(event) => setBody(event.target.value)}
        maxLength={4000}
        rows={4}
        placeholder="What stood out during your visit?"
        required
      />

      {error ? (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      ) : null}

      <div className="flex gap-2">
        <Button type="submit" size="sm" loading={submitting} className="rounded-full">
          Post review
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(false)}
          disabled={submitting}
          className="rounded-full"
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}
