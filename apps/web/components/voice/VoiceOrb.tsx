import { Loader2, Mic, MicOff, Volume2, Wrench } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { VoiceState } from "@/types/conversation";

const STATE_ICON: Partial<Record<VoiceState, typeof Mic>> = {
  LISTENING: Mic,
  SPEAKING: Volume2,
  TOOL_EXECUTING: Wrench,
  ERROR: MicOff,
};

const PULSING_STATES: VoiceState[] = ["LISTENING", "SPEAKING"];
const BUSY_STATES: VoiceState[] = ["CONNECTING", "THINKING", "TOOL_EXECUTING", "RECONNECTING"];

/**
 * Presentational-only state indicator. Never animates a "listening"
 * pulse unless the voice state actually says so — no fake waveform when
 * no audio is being captured/played (docs/AI_CONTEXT.md INV-10).
 */
export function VoiceOrb({ state, className }: { state: VoiceState; className?: string }) {
  const Icon = STATE_ICON[state] ?? Mic;
  const isBusy = BUSY_STATES.includes(state);
  const isPulsing = PULSING_STATES.includes(state);

  return (
    <div
      className={cn(
        "relative inline-flex size-10 items-center justify-center rounded-full transition-colors",
        state === "ERROR" ? "bg-danger-soft text-danger" : "bg-accent-soft text-accent",
        className,
      )}
    >
      {isPulsing ? (
        <span className="absolute inset-0 animate-ping rounded-full bg-accent/30" aria-hidden="true" />
      ) : null}
      {isBusy ? (
        <Loader2 className="size-4.5 animate-spin" aria-hidden="true" />
      ) : (
        <Icon className="size-4.5" aria-hidden="true" />
      )}
    </div>
  );
}
