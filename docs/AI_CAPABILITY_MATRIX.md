# AI Capability Matrix

Condensed view of `docs/AI_CAPABILITY_AUDIT.md`. Reflects the repository
as it exists today — not planned or aspirational features. "AI Tool"
means a Gemini function-calling tool already implemented and wired into
either the text-turn path, the voice tool-calls bridge, or both.

| Capability | Manual UI | Backend | AI Tool (text) | AI Tool (voice) | Mutates | Confirmation needed | Auth | Status |
|---|---|---|---|---|---|---|---|---|
| Search experiences (keyword/filter) | Yes | Yes | Yes (`search_experiences`) | Yes | No | No | None | Real |
| Semantic search + feasibility | No (not wired to `/discover` UI) | Yes (`POST /experiences/semantic-search`) | Via `search_experiences` (uses pipeline internally) | Via `search_experiences` | No | No | CurrentUser | Real, but `/discover` page doesn't use it — see audit §4 |
| Check feasibility for an experience | Indirect (surfaced inside compose/replan) | Yes (`POST /feasibility/check`) | Yes (`check_feasibility`) | **No — browser bridge only dispatches `search_experiences`** | No | No | CurrentUser | Backend real; voice path frontend-blocked |
| View experience detail | Yes | Yes (`GET /experiences/{id}`) | No dedicated tool | No | No | No | None | Real (no AI tool built yet) |
| Save experience (bookmark) | UI stub only | **None** | No | No | — | — | — | **UI-ONLY / NOT AI-AVAILABLE** |
| Unsave experience | UI stub only | **None** | No | No | — | — | — | **UI-ONLY / NOT AI-AVAILABLE** |
| View saved experiences | UI stub only (static empty state) | **None** | No | No | — | — | — | **UI-ONLY / NOT AI-AVAILABLE** |
| Submit a review | Yes (`WriteReviewForm`) | Yes (`POST /experiences/{id}/reviews`) | No dedicated tool | No | Yes | Should require confirmation if built | require_traveler | Real (no AI tool built yet) |
| View reviews/ratings | Yes | Yes (`GET /experiences/{id}/reviews`) | No dedicated tool | No | No | No | None | Real |
| Create itinerary (compose) | Yes (`/trip` composer) | Yes (`POST /itineraries/compose`) | Yes (`compose_experience`) | **No — browser bridge only dispatches `search_experiences`** | Yes | Yes | require_traveler | Backend real; voice path frontend-blocked |
| View itinerary | Yes (`/trip/[id]`) | Yes (`GET /itineraries/{id}`) | No dedicated tool | No | No | No | require_traveler + ownership | Real (no AI tool built yet) |
| View saved itineraries (trip list) | Yes (`/trip`) | Yes (`GET /itineraries`) | No dedicated tool | No | No | No | require_traveler | Real (no AI tool built yet) |
| Find similar itineraries | Yes | Yes (`POST /itineraries/similar`) | No dedicated tool | No | No | No | require_traveler | Real (no AI tool built yet) |
| Replan itinerary | Yes (manual replan action) | Yes (`POST /itineraries/{id}/replan`) | Yes (`replan_experience`) | **No — browser bridge only dispatches `search_experiences`** | Yes | Yes | require_traveler + ownership | Backend real; voice path frontend-blocked |
| Add item to itinerary | Yes | Yes (`POST /itineraries/{id}/items`) | No dedicated tool | No | Yes | Likely yes if built | require_traveler + ownership | Real (no AI tool built yet) |
| Cancel itinerary | Yes | Yes (`DELETE /itineraries/{id}`) | No dedicated tool | No | Yes | Yes if built | require_traveler + ownership | Real (no AI tool built yet) |
| Booking request | Yes | Yes (`POST /itineraries/{id}/booking-requests`) | No dedicated tool | No | Yes | Yes if built | require_traveler | Real — request/accept/decline only, **never** "confirmed" |
| Cancel booking | Yes | Yes (`POST /bookings/{id}/cancel`) | No dedicated tool | No | Yes | Yes if built | require_traveler + ownership | Real (no AI tool built yet) |
| Get weather context | Indirect (drives auto-replanning) | Yes (`GET /context/weather`) | No dedicated tool | No | No | No | CurrentUser | Real (no AI tool built yet) |
| Get events context | Indirect | Yes (`GET /context/events`) | No dedicated tool | No | No | No | CurrentUser | Real (no AI tool built yet) |
| Get nearby safety resources | Yes (`/safety`) | Yes (`GET /safety/resources/nearby`) | No dedicated tool | No | No | No | require_traveler | Real (no AI tool built yet) |
| Manage emergency contacts | Yes | Yes (CRUD) | No dedicated tool | No | Yes | Yes if built | require_traveler | Real (no AI tool built yet) |
| Trigger emergency alert | Yes (`EmergencyButton`) | Yes (`POST /safety/emergency-alerts`) | No dedicated tool | No | Yes | **Yes, always** | require_traveler | Real (no AI tool built yet) — sensitive action |
| Share location with contacts | UI stub (disabled button) | **None** | No | No | — | — | — | **UI-ONLY / NOT AI-AVAILABLE** — explicitly marked not implemented in UI copy |
| Live emergency service integration | UI copy only | **None** | No | No | — | — | — | **UI-ONLY / NOT AI-AVAILABLE** — explicitly marked not implemented |
| Add a local experience/place (traveler contribution) | **No** | **None** | No | No | — | — | — | **Does not exist anywhere** |
| Route / travel-time lookup | Indirect (map, itinerary) | Yes (`POST /location/route`, `/travel-time-matrix`) | No dedicated tool | No | No | No | None | Real (no AI tool built yet) |
| Geocode / reverse-geocode | Indirect (location pickers) | Yes (`GET /location/search`, `/reverse`) | No dedicated tool | No | No | No | None | Real (no AI tool built yet) |
| Nearby POIs (non-catalog) | Indirect | Yes (`GET /location/nearby-pois`) | No dedicated tool | No | No | No | None | Real (no AI tool built yet) — never promoted into catalog |

---

## Reading this table

- **"AI Tool (text)" / "AI Tool (voice)" = No** does not mean the
  capability is unavailable to travelers — it means no Gemini
  function-calling tool currently exposes it through either
  conversational path. The manual UI/API still works.
- **UI-ONLY / NOT AI-AVAILABLE** rows have no backend at all (saved
  experiences, contribution) or are explicitly, visibly disabled in the
  product itself (location sharing, live emergency integration). No tool
  should be built for these until the underlying capability is real.
- The **voice tool-call gap** (feasibility/compose/replan silently
  erroring over Gemini Live) is a single frontend fix
  (`apps/web/lib/voice/geminiLiveClient.ts::handleToolCalls`), not a
  backend limitation — the same backend route already serves all four
  tools correctly when called via the text/tool-calls REST path.
