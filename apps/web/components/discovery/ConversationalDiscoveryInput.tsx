"use client";

import { useId, useState } from "react";
import type { FormEvent } from "react";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { VoiceControlButton } from "@/components/voice/VoiceControlButton";
import { VoiceTranscriptPanel } from "@/components/voice/VoiceTranscriptPanel";
import { useTextConversation } from "@/hooks/useTextConversation";
import { useVoiceAgent } from "@/hooks/useVoiceAgent";
import type { DiscoveryState } from "@/types/discovery";

export interface ConversationalDiscoveryInputProps {
  size?: "hero" | "compact";
  suggestions?: string[];
  onSubmitQuery?: (query: string) => void;
  /** Real conversational discovery (Phase 5): fired with a deterministic
   * DiscoveryState patch derived from a text turn's extracted
   * TravelerContext, or a voice turn's search_experiences tool args. */
  onDiscoveryPatch?: (patch: Partial<DiscoveryState>) => void;
  className?: string;
}

const defaultSuggestions = [
  "3 hours in Fort with friends",
  "Local food under ₹1500",
  "Something cultural tonight",
  "Quiet places near me",
];

/**
 * Reusable conversational entry point for traveler intent (Phase 5: real
 * Gemini-backed text + voice discovery). Text submission still calls
 * onSubmitQuery (keyword search, unchanged) and additionally runs a real
 * conversational turn (Gemini extracts TravelerContext, the app
 * deterministically translates it into a DiscoveryState patch via
 * onDiscoveryPatch). The microphone button is a real Gemini Live voice
 * control — never a fake "coming soon" placeholder.
 */
export function ConversationalDiscoveryInput({
  size = "hero",
  suggestions = defaultSuggestions,
  onSubmitQuery,
  onDiscoveryPatch,
  className,
}: ConversationalDiscoveryInputProps) {
  const [value, setValue] = useState("");
  const inputId = useId();
  const isHero = size === "hero";

  const noopPatch = () => {};
  const { sendMessage } = useTextConversation(onDiscoveryPatch ?? noopPatch);
  const voice = useVoiceAgent(onDiscoveryPatch ?? noopPatch);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmitQuery?.(trimmed);
    void sendMessage(trimmed);
  }

  return (
    <div className={cn("w-full", className)}>
      <form
        onSubmit={handleSubmit}
        className={cn(
          "flex items-center gap-2 rounded-2xl border border-line-strong bg-surface p-2 shadow-[0_20px_50px_-25px_rgba(11,18,32,0.35)] transition-shadow focus-within:border-accent focus-within:shadow-[0_20px_50px_-20px_rgba(14,165,196,0.35)]",
          isHero ? "sm:p-2.5" : "",
        )}
        role="search"
      >
        <label htmlFor={inputId} className="sr-only">
          Describe what you&apos;re in the mood for
        </label>
        <input
          id={inputId}
          type="text"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="What are you in the mood for?"
          className={cn(
            "flex-1 bg-transparent px-3 text-ink placeholder:text-ink-subtle focus:outline-none",
            isHero ? "text-base sm:text-lg" : "text-sm",
          )}
        />
        <VoiceControlButton
          state={voice.state}
          isAvailable={voice.isAvailable}
          onStart={() => void voice.start()}
          onStop={voice.stop}
        />
        <button
          type="submit"
          disabled={!value.trim()}
          aria-label="Search experiences"
          className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-ink transition-opacity disabled:opacity-40"
        >
          <ArrowUp className="size-4.5" aria-hidden="true" />
        </button>
      </form>

      {voice.state !== "IDLE" ? (
        <div className="mt-3 space-y-2">
          <VoiceTranscriptPanel entries={voice.transcript} />
          {voice.errorMessage ? <p className="text-xs text-danger">{voice.errorMessage}</p> : null}
        </div>
      ) : null}

      {suggestions.length ? (
        <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Example prompts">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                setValue(suggestion);
                onSubmitQuery?.(suggestion);
              }}
              className="rounded-full border border-line bg-surface px-3.5 py-1.5 text-xs font-medium text-ink-muted transition-colors hover:border-accent hover:text-accent"
            >
              {suggestion}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
