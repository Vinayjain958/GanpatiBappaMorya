"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import { listSavedExperiences } from "@/lib/api/experiences";

const EMPTY_SET: Set<string> = new Set();

/**
 * The authenticated traveler's currently-saved experience ids, so grid
 * views (Discover) can render each ExperienceCard's bookmark button in
 * its real persisted state instead of always starting unsaved. Not used
 * for the /saved page itself, which renders full experience data rather
 * than just ids — see app/saved/page.tsx.
 */
export function useSavedExperienceIds(): Set<string> {
  const { isAuthenticated, user } = useAuth();
  const [savedIds, setSavedIds] = useState<Set<string>>(EMPTY_SET);
  const canFetch = isAuthenticated && user?.role === "traveler";

  useEffect(() => {
    // Nothing to fetch when logged out/not a traveler — and no setState
    // call needed either: the effect only ever needs to *add* real saved
    // ids once fetched, and a stale non-empty set from a previous
    // traveler on the same page instance is already cleared below by the
    // key change this hook's caller triggers on auth transitions (the
    // Discover/Saved pages remount their data on navigation/login
    // already), not by resetting state synchronously here.
    if (!canFetch) return;

    const controller = new AbortController();
    listSavedExperiences(controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) {
          setSavedIds(new Set(response.items.map((item) => item.id)));
        }
      })
      .catch(() => {
        // Saved-state is a UX nicety on the grid — a failed fetch just
        // leaves cards showing unsaved rather than breaking discovery.
      });

    return () => controller.abort();
  }, [canFetch]);

  return canFetch ? savedIds : EMPTY_SET;
}
