# Traveler Behavior and Demand Intelligence

## 1. Purpose and Scope

LocaLens is not only a system for finding local experiences; it is a system for understanding a traveler's situation and matching real experiences to that situation. This distinction is why traveler behavior and demand intelligence occupy a central place in the LocaLens domain: the same catalog of experiences can be more or less useful to a traveler depending on who they are, what they are trying to do right now, and what they have shown interest in before.

This document explains how traveler context, intent, preferences, behavior, feedback, and personalization operate on the traveler side of the ecosystem, and how individual traveler behavior aggregates into demand intelligence that is meaningful on the provider side. The two sides are connected: personalization uses a traveler's own signals to serve that traveler better, while demand intelligence uses many travelers' signals to help providers understand who is interested in their offering.

This document is distinct from the other documents in this corpus:

- **Document 1** (`01_LocaLens_Domain_Overview.md`) defines the overall LocaLens domain — travelers, providers, experiences, feasibility, and the core product loop. This document assumes that foundation and does not redefine it.
- **Document 2** (`02_Weather_Travel_Intelligence.md`) explains how weather and environmental conditions propagate through the travel ecosystem. This document touches weather only where it affects traveler behavior, and does not restate weather mechanics.
- A future Digital Twin document covers how traveler behavior, weather, and other real-world signals combine into an evolving system representation; this document only introduces where traveler behavior fits into that larger picture, without describing its implementation.
- A future document on social and public signals covers platform-specific and collection-level detail; this document does not.

---

## 2. The LocaLens Traveler

The traveler is the demand-side participant in the LocaLens ecosystem — the person whose intent, preferences, and constraints the system is trying to understand and serve.

LocaLens recognizes several traveler profiles as contextual shorthand:

- **Solo traveler** — a traveler exploring independently.
- **Friends group** — travelers exploring together.
- **Couple** — two travelers exploring together.
- **Family with children** — a group traveling with children.
- **Business traveler with free time** — a traveler with a constrained period available around business obligations.
- **Local explorer** — a resident discovering experiences in their own city.

These profiles describe a situation, not a fixed personality. They are contextual shorthand rather than deterministic behavioral labels: a profile indicates something about the traveler's circumstances (who they are traveling with, how much time they have, whether they are visiting or local), not a guarantee about what that traveler will want. The same person may behave differently in different situations — a solo traveler on one trip may be the same person traveling as part of a family group on another, and even within a single trip, the same traveler's priorities can shift from one part of the day to the next. Traveler behavior should be understood as situational, not as an immutable trait tied to a profile label.

---

## 3. Traveler Context

Traveler context is the structured representation of a traveler's current situation and expressed needs, as introduced in Document 1. It brings together several kinds of information:

- Current location
- Planned location or destination
- Available time
- Budget
- Group size
- Group composition
- Preferences
- Activity interests
- Accessibility requirements
- Constraints
- Conversational intent
- Current itinerary state
- Relevant real-world conditions (such as weather)

Traveler context is dynamic — it is not a single fixed profile captured once, but a live representation that can be updated as a session progresses, as the traveler provides new information, or as real-world conditions change.

It is useful to distinguish several layers within traveler context by how persistent they are:

- **Relatively persistent preferences** — general tendencies a traveler has shown or stated across time (for example, a general interest in cultural experiences).
- **Session-specific intent** — what the traveler is trying to accomplish in the current interaction (for example, "I want something for the next two hours").
- **Temporary constraints** — limits that apply to the current situation but are not permanent traits (for example, today's budget, or today's group size).
- **Current situational context** — facts about right now, such as current location or current weather.

A critical rule applies across all of these layers: not every context value is always known. An unknown value is different from a false or negative one. If a traveler's accessibility needs are not stated, that does not mean the traveler has no accessibility needs — it means the system does not know. Treating "unknown" as equivalent to "no" or "none" would silently misrepresent the traveler's actual situation.

---

## 4. Traveler Intent

Traveler intent is what the traveler is trying to accomplish, as expressed through natural language, voice, or other interaction. Several kinds of intent can appear in the LocaLens domain:

- **Explicit intent** — directly stated, such as "I want something cultural."
- **Implied intent** — suggested by context or phrasing without being stated outright.
- **Exploratory intent** — a traveler browsing possibilities without a narrow goal yet.
- **Goal-oriented intent** — a traveler working toward a specific outcome, such as filling a specific time window.
- **Situational intent** — intent shaped by the immediate situation, such as weather or a schedule change.
- **Follow-up intent** — intent expressed in response to a previous system output, refining or narrowing it.
- **Replanning intent** — intent expressed because circumstances changed after a plan was already made.

Representative, generic examples of expressed intent:

- "I want something cultural nearby."
- "I have 90 minutes."
- "It is raining, so I would rather stay indoors."
- "I want something under my budget."
- "I want something suitable for my group."

A single statement can carry several pieces of intent and context simultaneously — a time constraint, an activity preference, and a reaction to current conditions can all appear in one sentence. Intent is also not static within a session: a traveler's expressed intent can change as the conversation continues, as new information becomes available, or as the traveler reconsiders their situation.

---

## 5. Preferences vs Constraints

This distinction is one of the most important in the traveler behavior domain.

**Preference** — something the traveler generally or currently favors. A preference shapes what is more or less desirable among options that already work.

**Constraint** — a condition that limits what can actually work. A constraint determines whether an option is usable at all.

Examples:

- Preferring outdoor experiences is a preference.
- Not being able to exceed the available time is a constraint.
- Liking cultural experiences is a preference.
- An accessibility requirement is potentially a hard constraint.
- Preferring low-cost activities is a preference.
- An explicit maximum budget is a constraint.

Preferences help rank or personalize among options that are already feasible. Constraints participate in feasibility itself, as described in Document 1's feasibility framework. A preference signal must never be allowed to silently override a hard constraint — no matter how strongly a traveler seems to prefer an outdoor experience, that preference cannot make an accessibility requirement or a budget limit disappear. Preferences adjust ordering and emphasis; constraints determine whether something is possible in the first place.

---

## 6. Group Composition and Collective Behavior

Group composition changes what kind of experience makes sense for a given trip. Solo travel, couples, friends groups, families with children, business travelers with limited free time, and mixed-interest groups each bring a different situational context to discovery and planning.

Group context may affect:

- Activity suitability (whether an experience type fits the group)
- Pacing (how much can reasonably be scheduled)
- Budget interpretation (a stated budget may apply per person or across the whole group)
- Travel distance tolerance
- Preferred experience type
- Timing
- Accessibility needs
- Coordination complexity (more participants can mean more constraints to satisfy simultaneously)

It should not be assumed that every member of a group behaves identically or shares the same preferences. A friends group or family may include people with different interests, and the traveler context expressed to the system may represent a compromise or a shared decision rather than any one individual's ideal choice. Group decisions can involve competing preferences that get resolved before or during the interaction with LocaLens, and the system should treat the expressed group intent as the relevant signal rather than assuming internal uniformity.

---

## 7. Time, Budget, Location, and Practical Constraints

Travelers make choices under real-world limits, and these limits shape behavior directly. Relevant practical factors include:

- Limited available time
- Travel distance
- Route burden (the cumulative effort of moving between experiences)
- Budget
- Opening or operating conditions
- Availability
- Capacity
- Accessibility
- Itinerary conflicts
- Changing conditions

A central principle governs this section, carried over from Document 1:

**RELEVANCE ≠ FEASIBILITY**

An experience can be exactly what a traveler is looking for in terms of topic and preference, and still be unusable because it does not fit the time available, is too far away, exceeds the budget, or conflicts with another planned activity. This document does not repeat the full feasibility framework described in Document 1; the point here is narrower — that these practical limits are also a major shaper of traveler behavior itself. A traveler who has limited time will naturally gravitate toward shorter or closer options; a traveler with a tight budget will naturally avoid options that exceed it. Practical constraints are not just a backend filter — they are part of what a traveler is actually reasoning about when choosing among experiences.

---

## 8. Traveler Choice and Evaluation

When a traveler evaluates candidate experiences, several conceptual factors can inform that evaluation:

- Match to stated intent
- Preference alignment
- Group suitability
- Time compatibility
- Budget compatibility
- Accessibility compatibility
- Location and travel burden
- Current context
- Weather or environmental conditions
- Known experience characteristics
- Previous behavior

Travelers often compare alternatives against each other rather than evaluating each candidate experience in isolation — a choice is frequently relative to what else is available, not made in a vacuum. It is also important to recognize that a recommendation can become less attractive even when the experience itself has not changed at all, simply because the traveler's context has changed. An experience that was perfectly suitable an hour ago may no longer make sense if the traveler's available time has shrunk, the weather has shifted, or the group composition has changed — the experience is unchanged, but its fit to the current context is not.

---

## 9. Personalization

Personalization in LocaLens means adapting candidate ranking or presentation to a specific traveler's context and demonstrated preferences, building on the general personalization concept introduced in Document 1.

Personalization can draw on:

- Current context
- Stated preferences
- Historical interaction signals
- Saved experiences
- Completed experiences
- Ratings
- Reviews
- Itinerary behavior
- Repeated patterns

Personalization in LocaLens is a behavior-based concept: it works from observed and stated signals about the traveler rather than from an abstract, universal model of what all travelers want. This document does not claim that personalization requires any specific machine-learning architecture, and no scoring weights, formulas, or model names are established here — those are implementation-level details outside the scope of a domain corpus document.

It is useful to distinguish two related but different questions:

- **Relevance** asks whether an experience fits the current request and context.
- **Personalization** asks how well an experience matches this particular traveler, given what is known about them beyond the immediate request.

An experience can be relevant to a stated request without being especially personalized to the individual traveler, and personalization refines the ordering of already-relevant, already-feasible candidates rather than replacing relevance or feasibility.

---

## 10. Traveler Feedback Signals

Feedback is evidence generated through traveler interaction with the system. Conceptual signals include:

- Views
- Clicks or interactions
- Saves
- Unsaves
- Completions or visits
- Ratings
- Reviews
- Itinerary additions
- Itinerary removals
- Repeated interest in the same or similar experiences
- Rejection or avoidance signals, where explicitly available

Different signals carry different meanings and different strength as evidence. Viewing an experience indicates attention, but not necessarily preference — a traveler may view something out of curiosity without wanting it. Saving may indicate stronger interest than viewing alone. Completion — actually experiencing something — is stronger evidence of genuine participation than any earlier-stage signal. A rating expresses an explicit evaluation, made deliberately by the traveler. A review provides richer, qualitative feedback beyond a single score.

This document does not assign specific numerical strengths or weights to these signals; the important domain concept is the relative ordering of confidence — an explicit rating or a completed visit is stronger evidence than a single view — rather than a specific formula for combining them.

---

## 11. Positive, Negative, and Ambiguous Signals

Behavioral signals are frequently ambiguous rather than clearly positive or negative. Consider:

- An experience is viewed but not saved.
- An experience is saved, then later removed.
- An experience is recommended but ignored.
- An experience is completed without being rated.
- A low rating is given despite the experience being completed.
- The same experience is viewed repeatedly.

Each of these situations admits more than one explanation. Behavior should be interpreted cautiously rather than confidently. A missing action does not automatically mean dislike — a traveler might not save something simply because they were still deciding, not because they rejected it. An explicit negative signal (such as a low rating, or an explicit "not interested" action where the system supports one) should be treated as meaningfully different from mere absence of engagement, which carries much weaker and more ambiguous evidential value.

This distinction matters because overconfident personalization — treating every absence of action as a rejection, or every single view as proof of a stable preference — risks systematically misunderstanding travelers rather than serving them better.

---

## 12. Learning From Traveler Behavior

Repeated traveler behavior can inform future personalization through a conceptual flow:

OBSERVED BEHAVIOR
→ SIGNAL
→ PREFERENCE EVIDENCE
→ UPDATED TRAVELER UNDERSTANDING
→ FUTURE PERSONALIZATION

This process is not necessarily permanent or one-directional. Traveler preferences can change across several dimensions:

- By trip
- By time
- By group
- By season
- By weather
- By budget
- By current objective
- By location

Because preferences can shift for any of these reasons, historical behavior should not blindly override current explicit intent. Learning from behavior means building an evolving, updatable understanding of a traveler — not locking in a fixed profile that is assumed to hold indefinitely.

---

## 13. Current Intent vs Historical Preference

This distinction must be made explicit, because it directly affects how a traveler is served in the moment.

A traveler may have a historical pattern that differs from what they are asking for right now.

Example:

Historical pattern — the traveler often chooses indoor cultural experiences.

Current request — "I want an outdoor walk today."

In this situation, the current explicit request should be treated as relevant context, not overridden by the historical pattern. The system should not force historical behavior onto a request that clearly states something different. No fixed ranking formula is defined here for resolving this tension in every case; the guiding principle is:

CURRENT EXPRESSED INTENT + CURRENT CONTEXT + RELEVANT HISTORICAL SIGNALS

rather than:

HISTORICAL BEHAVIOR ONLY

Historical signals remain useful — they can help disambiguate an underspecified request, or surface options the traveler might not have thought to ask for — but they support the current request; they do not supersede it.

---

## 14. Traveler Behavior Under Changing Conditions

Traveler behavior can change when the surrounding environment changes. Relevant conceptual changes include:

- Weather changes
- Available time changes
- Budget changes
- Location changes
- Group composition changes
- Experience availability changes
- Route condition changes
- Itinerary progress changes

The general relationship is:

CHANGED CONDITION
→ CHANGED CONTEXT
→ CHANGED PREFERENCE/PRIORITY
→ CHANGED EXPERIENCE CHOICE
→ POSSIBLE REPLANNING

This mirrors the dynamic adaptation concept from Document 1 and connects to Document 2's weather-impact framework, but this document focuses specifically on the traveler-behavior side of that relationship — how a changed condition shows up as a changed choice or a changed request — rather than restating how weather impact itself is technically evaluated.

---

## 15. Demand Intelligence

Demand intelligence is the traveler-side counterpart to personalization: rather than serving one traveler better, it aggregates many travelers' interactions into evidence that is useful to providers and to the broader ecosystem.

The conceptual flow is:

INDIVIDUAL INTERACTIONS
→ AGGREGATED PATTERNS
→ DEMAND SIGNALS
→ PROVIDER INSIGHT

Possible dimensions of demand include:

- Interest by experience category
- Interest by traveler profile type
- Interest by location
- Timing patterns (when interest occurs)
- Budget patterns
- Contextual demand (demand that varies with conditions such as weather or season)
- Repeated interest in the same or similar experiences
- Conversion or engagement patterns (how interest translates into deeper interaction)

No specific numerical demand metrics, production statistics, or unavailable data claims are established in this document — the concept is that individual, real interactions can be aggregated into patterns; the specific measurement approach is an implementation detail outside this corpus.

---

## 16. Individual Preference vs Aggregate Demand

This distinction must be kept clear, since the two concepts are easy to conflate.

**Individual preference** answers: "What does this particular traveler tend to prefer?"

**Aggregate demand** answers: "What patterns appear across many travelers?"

Aggregate demand should not be assumed to automatically represent every individual traveler within it — a pattern that holds broadly may not apply to any specific person. Symmetrically, one individual traveler's behavior should not be treated as statistically representative of the entire traveler population. Personalization draws on individual signals; demand intelligence draws on aggregated signals; the two serve different purposes and should not be substituted for one another.

---

## 17. Traveler–Provider Matching

Traveler-provider matching connects the demand side and the supply side of the LocaLens ecosystem, as introduced in Document 1.

Traveler side:

intent → preferences → constraints → behavior

Provider side:

experience characteristics → availability → operational information → offering

Matching is the conceptual process of identifying meaningful compatibility between these two sides — recognizing that a traveler's context and an experience's characteristics fit well together. Matching does not mean guaranteeing a booking or a confirmed outcome; it means identifying a candidate connection worth surfacing. No specific matching algorithm or scoring function is defined in this document; the concept is the relationship itself, not its computational realization.

---

## 18. Demand Changes and Market Feedback

Traveler behavior can create a feedback loop into the provider ecosystem:

TRAVELER INTEREST
→ EXPERIENCE ENGAGEMENT
→ DEMAND SIGNAL
→ PROVIDER VISIBILITY
→ PROVIDER UNDERSTANDING
→ POSSIBLE OFFERING ADJUSTMENT
→ FUTURE TRAVELER RESPONSE

It should not be claimed that providers automatically change their offerings in response to demand signals — a provider may or may not act on the insight available to them. Language describing this loop should use "may," "can," or "could" rather than asserting a guaranteed response, since the actual decision to adjust an offering rests with the provider, not with the system.

---

## 19. Weather and Traveler Behavior

Weather, as described in detail in Document 2, is one contextual variable that can influence traveler behavior. Relevant conceptual effects include:

- Preference shifting between indoor and outdoor experiences
- Willingness to travel farther changing
- Timing preferences shifting
- Route tolerance changing
- Increased demand for alternatives
- Changing interest in events or activities

This document does not restate Document 2's weather-impact mechanics (impact classification, direct/secondary/cascading effects, or geographic propagation); it only notes that weather is one input among several that can shape a traveler's expressed intent and choices. Weather should be treated as one contextual variable among many, not as an automatic explanation for every behavioral change a traveler shows — the same weather condition can affect different travelers differently, or may not be the actual cause of a given change in behavior at all.

---

## 20. Traveler Behavior and the Digital Twin

Traveler behavior can form one dynamic component of a broader, evolving system representation — a Digital Twin, as introduced conceptually in Document 2 — that models how the target ecosystem behaves under changing conditions.

Such a representation can conceptually incorporate:

- Traveler context
- Experience state
- Itinerary state
- Route state
- Weather and environmental conditions
- Social or public signals
- Demand signals
- Provider-side context

Traveler behavior is one dynamic input into this larger, interconnected picture — it does not constitute the entire representation on its own, just as weather alone does not. This document introduces the relationship at a conceptual level only; the implementation-oriented details of how such a system representation is constructed and maintained belong to a separate document in this corpus.

---

## 21. Uncertainty and Behavioral Inference

This section is critical to how traveler behavior should be interpreted throughout the LocaLens domain.

**Observed behavior ≠ certain motivation.**

Examples:

- A traveler does not save an experience — the underlying motivation is unknown; it could reflect disinterest, indecision, or simple oversight.
- A traveler views an experience once — this suggests possible interest, but does not prove a stable preference.
- A traveler gives a low rating — this is comparatively strong evidence of a negative evaluation, because it is an explicit, deliberate signal.
- A traveler changes their plan — the behavior itself is observed, but the exact reason may remain unknown unless the traveler states it.

Reasoning about traveler behavior should distinguish among:

- **KNOWN** — directly stated or explicitly recorded.
- **INFERRED** — reasonably suggested by a pattern of behavior, but not stated directly.
- **UNCERTAIN** — plausible but weakly supported.
- **UNKNOWN** — no meaningful evidence available.

Inferred motivation must never be presented as fact. A behavioral pattern can support a reasonable inference, but that inference remains an inference — it should be labeled and treated as such, not stated with the same confidence as an explicit traveler statement.

---

## 22. AI and Domain Intelligence Boundaries

AI or domain intelligence operating on traveler behavior may:

- Interpret stated traveler intent
- Summarize traveler context
- Identify behavioral patterns
- Interpret feedback signals
- Identify possible preference patterns
- Explain demand patterns
- Reason about contextual changes
- Summarize matching factors
- Explain why an experience may align with stated preferences

AI must NOT:

- Invent traveler preferences
- Invent traveler actions
- Fabricate reviews or ratings
- Fabricate demand statistics
- Claim an experience was completed when it was not recorded
- Override deterministic feasibility
- Invent availability
- Infer sensitive personal attributes without evidence
- Treat uncertain behavioral inference as verified fact
- Silently convert a weak behavioral signal into a hard constraint

This preserves the same architectural boundary used throughout the LocaLens domain: AI assists understanding and interpretation of traveler behavior; deterministic backend systems remain authoritative for actual traveler state, actual feasibility, and actual decisions.

---

## 23. Conceptual Behavior Examples

**Example A.**
A traveler asks for cultural experiences. The system retrieves relevant candidates. The traveler saves one. Future personalization can treat that save as an interest signal.

**Example B.**
A traveler repeatedly chooses experiences within a limited time window. This can provide evidence of a preference for shorter activities, but should not become an absolute rule applied to every future request from that traveler.

**Example C.**
A traveler historically prefers outdoor experiences, but a current rainy-day request favors indoor alternatives. The current context changes the immediate preference expression, and the current request should be honored accordingly.

**Example D.**
Several travelers interact with the same local experience. The aggregated behavior across these travelers may form a demand signal relevant to the provider side, distinct from any one traveler's individual preference.

**Example E.**
A traveler views an experience but does not save it. This is an ambiguous signal and should not automatically be interpreted as rejection.

**Example F.**
A traveler removes an experience from an itinerary after weather changes. This indicates that the plan changed, but the exact motivation should not be invented beyond what is actually known or stated.

All examples above are generic illustrations of behavioral reasoning patterns. No real businesses, statistics, or specific traveler datasets are represented.

---

## 24. Domain Relationships Summary

Three conceptual chains summarize the relationships covered in this document.

**Individual personalization chain:**

TRAVELER
→ CONTEXT
→ INTENT
→ PREFERENCES
→ CONSTRAINTS
→ EXPERIENCE INTERACTION
→ FEEDBACK
→ BEHAVIOR SIGNALS
→ PERSONALIZATION

A traveler's situation and expressed intent, filtered through their preferences and constraints, leads to interaction with specific experiences; that interaction generates feedback and behavior signals, which in turn inform how future personalization serves that same traveler.

**Demand intelligence chain:**

TRAVELER INTERACTIONS
→ AGGREGATED DEMAND
→ PROVIDER INTELLIGENCE
→ TRAVELER–PROVIDER MATCHING

Many individual travelers' interactions aggregate into demand patterns; those patterns become intelligence useful to providers; and that intelligence supports better matching between traveler demand and provider supply going forward.

**Adaptation chain:**

REAL-WORLD CONDITIONS
→ CONTEXT CHANGE
→ BEHAVIOR CHANGE
→ DEMAND CHANGE
→ POSSIBLE REPLANNING

Conditions in the real world (such as weather, timing, or availability) change a traveler's context; that context change can shift behavior; behavior shifts in turn can be reflected in demand patterns; and any of these changes can trigger a reassessment of an existing plan.

---

## 25. Domain Vocabulary

**Traveler** — A person seeking to discover, evaluate, plan, or experience local activities; the demand-side participant in the LocaLens ecosystem.

**Traveler Context** — The structured, dynamic representation of a traveler's current situation and expressed needs.

**Traveler Profile** — A contextual shorthand category (such as solo traveler or family with children) describing a traveler's situation, not a fixed personality trait.

**Traveler Intent** — What a traveler is trying to accomplish, as expressed through language or interaction.

**Preference** — Something a traveler generally or currently favors; informs ranking among feasible options.

**Constraint** — A condition that limits what can actually work; participates in feasibility.

**Group Composition** — The makeup of the traveler's party (solo, couple, friends, family, and so on) and its effect on suitable experiences.

**Personalization** — Adapting candidate ranking or presentation to a specific traveler's context and demonstrated preferences.

**Behavioral Signal** — Evidence generated through traveler interaction (viewing, saving, completing, rating, and similar actions).

**Feedback Signal** — A behavioral signal specifically interpreted as evidence relevant to preference or evaluation.

**Explicit Feedback** — Deliberate, direct traveler evaluation, such as a rating or review.

**Implicit Feedback** — Indirect evidence inferred from behavior, such as views or saves, without an explicit evaluative statement.

**Preference Evidence** — Any signal (explicit or implicit) that supports an inference about what a traveler favors.

**Historical Preference** — A pattern of preference evidenced across past behavior.

**Current Intent** — What the traveler is expressing or requesting right now, in the present interaction.

**Demand** — The pattern of traveler interest in experiences, categories, or locations.

**Demand Signal** — A discrete piece of evidence contributing to an understanding of demand.

**Aggregate Demand** — Demand patterns formed by combining signals across many travelers, as opposed to one individual.

**Traveler–Provider Matching** — The conceptual process of identifying meaningful compatibility between traveler demand and provider supply.

**Behavioral Inference** — A conclusion drawn from observed behavior that is not itself a directly stated fact.

**Uncertainty** — The degree to which a piece of information or inference is not fully certain.

**Observed Behavior** — An action or event that has actually occurred and been recorded, as distinct from an inferred motivation behind it.

**Digital Twin State** — The continuously evolving virtual representation of the system's real-world entities and conditions, of which traveler behavior is one dynamic component.

---

## 26. AI-System Boundaries

AI or domain intelligence MAY:

- Understand expressed intent
- Interpret contextual behavior
- Identify possible preference patterns
- Summarize feedback
- Explain demand patterns
- Reason about possible matching
- Describe uncertainty

Deterministic/backend systems remain authoritative for:

- Actual traveler account state
- Actual saved state
- Actual review/rating records
- Actual itinerary state
- Actual experience state
- Actual availability
- Actual booking/request state
- Actual feasibility
- Actual database mutations

The model must never manufacture missing traveler activity or infer unsupported facts. As with the rest of the LocaLens domain, AI assists interpretation and explanation of traveler behavior; it does not become the authoritative source of actual traveler state, actual feasibility, or actual system decisions.

---

*Source note: This document was derived from the LocaLens project's product, architecture, and current implementation documentation (traveler context, personalization, ranking, feedback/interaction, and review concepts), together with Documents 1 and 2 of this alignment corpus, for the purpose of domain-alignment corpus creation. It describes stable conceptual relationships and does not represent a specific implementation status at any point in time.*
