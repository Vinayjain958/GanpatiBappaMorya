"use client";

import { useCallback, useRef, useState } from "react";
import { createConversation, issueLiveToken } from "@/lib/api/conversation";
import { ApiError } from "@/lib/api/client";
import { isMicrophoneSupported } from "@/lib/voice/audioCapture";
import { GeminiLiveClient } from "@/lib/voice/geminiLiveClient";
import { searchArgsToDiscoveryPatch } from "@/lib/discovery/travelerContextToPatch";
import type { DiscoveryState } from "@/types/discovery";
import type { SearchExperiencesArgs, VoiceState, VoiceTranscriptEntry } from "@/types/conversation";

/**
 * Composes real mic capture + playback + Gemini Live connection into one
 * hook. Voice is only ever started by an explicit user action (start()) —
 * never auto-connected on mount. Any unrecoverable failure lands in
 * ERROR, never a faked CONNECTED state (see docs/DECISIONS.md ADR-034).
 */
export function useVoiceAgent(onDiscoveryPatch: (patch: Partial<DiscoveryState>) => void) {
  const [state, setState] = useState<VoiceState>("IDLE");
  const [transcript, setTranscript] = useState<VoiceTranscriptEntry[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const clientRef = useRef<GeminiLiveClient | null>(null);
  const conversationIdRef = useRef<string | null>(null);

  const isAvailable = isMicrophoneSupported();

  const handleTranscript = useCallback((entry: VoiceTranscriptEntry) => {
    setTranscript((prev) => {
      // Merge incremental fragments of the same in-progress turn rather
      // than appending a new row per partial transcript event.
      const last = prev[prev.length - 1];
      if (last && last.role === entry.role && !last.final) {
        return [...prev.slice(0, -1), entry];
      }
      return [...prev, entry];
    });
  }, []);

  const handleToolResultApplied = useCallback(
    (args: Record<string, unknown>) => {
      onDiscoveryPatch(searchArgsToDiscoveryPatch(args as SearchExperiencesArgs));
    },
    [onDiscoveryPatch],
  );

  const start = useCallback(async () => {
    if (!isAvailable) {
      setState("ERROR");
      setErrorMessage("Voice isn't supported in this browser.");
      return;
    }

    setErrorMessage(null);
    setState("CONNECTING");

    try {
      if (!conversationIdRef.current) {
        const conversation = await createConversation();
        conversationIdRef.current = conversation.id;
      }

      const tokenResponse = await issueLiveToken();

      const client = new GeminiLiveClient(conversationIdRef.current, {
        onStateChange: setState,
        onTranscript: handleTranscript,
        onToolResultApplied: handleToolResultApplied,
        onError: setErrorMessage,
      });
      clientRef.current = client;
      await client.connect(tokenResponse.token, tokenResponse.model);
    } catch (error) {
      setState("ERROR");
      setErrorMessage(
        error instanceof ApiError && error.status === 503
          ? "Live voice is not available right now."
          : "Couldn't start voice.",
      );
    }
  }, [handleToolResultApplied, handleTranscript, isAvailable]);

  const stop = useCallback(() => {
    clientRef.current?.disconnect();
    clientRef.current = null;
    setState("IDLE");
  }, []);

  return { state, transcript, errorMessage, start, stop, isAvailable };
}
