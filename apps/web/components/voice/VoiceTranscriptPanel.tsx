import { cn } from "@/lib/utils/cn";
import type { VoiceTranscriptEntry } from "@/types/conversation";

export function VoiceTranscriptPanel({
  entries,
  className,
}: {
  entries: VoiceTranscriptEntry[];
  className?: string;
}) {
  if (entries.length === 0) return null;

  return (
    <div
      role="log"
      aria-live="polite"
      aria-label="Voice conversation transcript"
      className={cn("max-h-48 space-y-2 overflow-y-auto rounded-xl border border-line bg-surface-sunken p-3", className)}
    >
      {entries.map((entry, index) => (
        <p key={index} className="whitespace-pre-wrap break-words text-sm">
          <span className={cn("font-medium", entry.role === "user" ? "text-ink" : "text-accent")}>
            {entry.role === "user" ? "You: " : "LocaLens: "}
          </span>
          <span className="text-ink-muted">{entry.text}</span>
        </p>
      ))}
    </div>
  );
}
