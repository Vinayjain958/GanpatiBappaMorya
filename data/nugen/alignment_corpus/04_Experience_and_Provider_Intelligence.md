# Experience and Provider Intelligence

## 1. Purpose and Scope

LocaLens is not useful merely because it can retrieve a local place; the system needs to understand what a place or activity actually offers, under what conditions it can actually be used, and how that offering relates to a traveler's needs. Retrieving a name and a location is not the same as understanding an experience.

Experience and provider intelligence forms the supply-side foundation that other parts of the LocaLens domain depend on:

- Discovery needs to know what an experience is before it can be surfaced.
- Feasibility needs experience-level facts (hours, price, capacity, accessibility) to evaluate against traveler constraints.
- Personalization needs experience characteristics to match against traveler preferences.
- Itinerary composition needs experience-level timing and location facts to build a coherent plan.
- Provider intelligence needs to understand what a provider actually offers before it can report meaningful demand insight.
- Traveler-provider matching needs a clear picture of supply before it can connect it to demand.
- Weather- and context-aware reasoning needs to know an experience's characteristics before it can reason about environmental effects on it.
- Dynamic adaptation needs to detect when an experience's state has actually changed.

This document focuses specifically on the entity and supply-side meaning of an experience and a provider — what they are, what characterizes them, how their state can change, and how that state should be reasoned about. It builds on the domain foundation in `01_LocaLens_Domain_Overview.md`, the weather concepts in `02_Weather_Travel_Intelligence.md`, and the traveler-behavior concepts in `03_Traveler_Behavior_and_Demand_Intelligence.md`, without restating their full frameworks.

---

## 2. The Local Experience as the Core Supply Entity

A local experience may represent:

- A place
- A venue
- An activity
- An event
- A local offering
- A service-like experience
- A destination-specific activity that can be discovered and potentially visited

The experience is the central bridge connecting the two sides of the LocaLens ecosystem:

PROVIDER
→ offers
→ EXPERIENCE
→ discovered by
→ TRAVELER

An experience is not merely a map coordinate or a search result row. It carries semantic characteristics (what it is and what category it belongs to), spatial characteristics (where it is), temporal characteristics (when it can be used), operational characteristics (whether it is currently usable), and contextual characteristics (how conditions around it affect its suitability). Understanding an experience means understanding all of these dimensions together, not just its name and location.

---

## 3. Experience Identity and Characteristics

An experience may be described by a range of conceptual attributes, where applicable:

- Name
- Category
- Description
- Location
- Geographic area
- Price or pricing information
- Duration
- Operating information
- Availability
- Capacity
- Accessibility
- Environmental characteristics
- Activity characteristics
- Suitability characteristics
- Media
- Ratings and reviews, when available

A critical distinction runs through all reasoning about experience characteristics:

**EXPERIENCE FACT vs. INFERRED CHARACTERISTIC**

A recorded fact is something directly known about the experience — for example, "indoor venue." An inferred characteristic is a conclusion drawn from that fact — for example, "likely less exposed to rain." The inference may be reasonable, but it is interpretation, not a directly recorded fact about the experience itself. Experience attributes (what is actually known or recorded) must not be confused with conclusions derived from them (what can be reasonably inferred). Keeping this distinction explicit prevents an inference from silently being treated with the same confidence as a recorded fact.

---

## 4. Experience Taxonomy

These twenty categories constitute the current LocaLens experience taxonomy:

- **food-drink** — general dining and beverage experiences, restaurants and eateries.
- **street-food** — informal, vendor-based, or street-level food experiences.
- **cafes** — café and coffee-shop experiences.
- **culture-heritage** — cultural and heritage sites reflecting local history or tradition.
- **art-galleries** — venues exhibiting visual art.
- **museums** — institutions preserving and displaying collections or exhibits.
- **workshops** — hands-on instructional sessions where travelers learn a skill.
- **crafts** — experiences centered on traditional or artisanal craftwork.
- **shopping-markets** — markets, bazaars, and shopping-oriented local venues.
- **outdoors** — outdoor activities and natural settings.
- **adventure** — higher-intensity or thrill-oriented outdoor activities.
- **photography** — experiences oriented around scenic or photogenic value.
- **family** — experiences suited to travelers with children.
- **nightlife** — evening and night-oriented social experiences.
- **music** — live music and music-oriented venues or events.
- **community** — community-oriented gatherings or local social activities.
- **hidden-gems** — lesser-known local experiences off the typical path.
- **wellness** — health, relaxation, and wellness-oriented experiences.
- **entertainment** — general entertainment venues and activities.
- **local-experiences** — distinctly local, place-specific experiences not captured by other categories.

Each category description above is a neutral statement of what the category represents; none implies anything about a category's popularity, demand level, or how a specific traveler will feel about it. A category is a classification label, not a prediction of traveler behavior.

---

## 5. Experience Context and Environment

The same experience can carry different practical implications depending on the context surrounding it. Relevant contextual dimensions include:

- Location
- Time
- Surrounding environment
- Weather
- Route access
- Traveler context
- Group composition
- Current availability
- Operational state

An experience characteristic does not automatically determine suitability on its own. Being outdoors does not automatically mean an experience becomes unsuitable in bad weather — the degree of exposure, the specific weather condition, and the traveler's own tolerance all matter. Being indoors does not automatically mean an experience is feasible — an indoor experience can still be closed, full, or otherwise unusable. Suitability must always be reasoned about in light of the broader context, not read directly off a single characteristic.

---

## 6. Experience Suitability

Experience suitability is the degree to which an experience fits a traveler and the current context. The conceptual relationship is:

EXPERIENCE CHARACTERISTICS
+ TRAVELER CONTEXT
+ CURRENT CONDITIONS
→ CONTEXTUAL SUITABILITY

It is important to separate two related ideas:

- The **intrinsic characteristics** of an experience — what it is, where it is, what category it belongs to — which remain relatively stable.
- Its **contextual suitability** at a particular moment — how well it fits a specific traveler under specific current conditions — which can change frequently.

An experience does not become a permanently "good" or "bad" experience merely because one condition changes. A museum that is a poor fit for a traveler with fifteen minutes available is not thereby a poor museum — it is simply a poor fit for that traveler's current time constraint. Suitability is contextual, not an intrinsic verdict on the experience itself.

---

## 7. Operational State of an Experience

Experience state can change over time. Conceptual states relevant to this domain include:

- Available
- Unavailable
- Open / operating
- Closed / not operating
- Capacity-limited
- Conditionally usable
- Uncertain / unknown

Additional states beyond what the project actually documents should not be invented. State should always come from actual evidence — a recorded status, a confirmed observation, or an explicit signal — rather than assumption. A model must not infer that unknown availability means available; when the required fact is unavailable, the correct representation is **UNKNOWN**, not a favorable guess.

---

## 8. Availability

Availability is a nuanced concept with several distinct layers, which should not be collapsed into one another:

- **Existence** of the experience (it is a real, catalogued offering)
- **Operating / open status** (whether it is currently running at all)
- **Current availability** (whether it can be used right now)
- **Future availability** (whether it can be used at some later time)
- **Capacity availability** (whether there is room, even if it is open)
- **Booking or request availability**, where applicable (whether a request for it can currently be made)

These are not identical, and conflating them produces incorrect conclusions. An experience can exist but be closed. An experience can be open but full. An experience can normally operate on a regular schedule but still lack verified current availability at this specific moment. Availability is a real-world fact, and it must not be fabricated or assumed favorably when it is not actually known.

---

## 9. Opening and Operating Conditions

Operating information plays a specific conceptual role, distinct from availability itself. Relevant concepts include:

- Opening times
- Operating windows
- Scheduled times
- Event timing
- Temporary closure
- Changed operating conditions
- Unknown operating information

A key clarification applies here:

UNKNOWN HOURS ≠ OPEN

UNKNOWN HOURS ≠ CLOSED

When operating information is not known, neither a positive nor a negative assumption is warranted. No numerical fallback assumption (such as defaulting to "probably open during typical hours") should be introduced. Actual operating information should come only from authoritative available data — recorded hours, a confirmed schedule, or an explicit status — not from a plausible-sounding default.

---

## 10. Capacity and Resource Constraints

Capacity is the concept of how much an experience can accommodate at a given time — participant capacity, space limitations, resource limitations, and compatibility with a given group size. A related concept is simultaneous demand: whether other travelers or groups are also competing for the same limited capacity.

An important relationship to keep separate:

EXPERIENCE SUITABILITY may be high

while

CAPACITY FEASIBILITY may be low.

An experience can be an excellent match for a traveler's interests and context, and still be infeasible at a specific moment because it lacks the capacity to accommodate the traveler's group. Capacity should be treated as a separate, factual, operational attribute — never inferred from an experience's popularity, physical size, category, or other general assumptions. Capacity facts come from actual recorded or observed information, not from reasoning about what capacity "probably" is.

---

## 11. Pricing and Budget Relevance

Pricing interacts directly with traveler budget constraints, but the two concepts remain distinct: pricing is an attribute of the experience or provider offering, while budget is a traveler-side constraint (as described in Document 3).

Relevant pricing concepts include:

- A known, specific price
- A price range
- Group pricing
- Per-person pricing
- Unknown pricing
- Contextual cost information, where documented

No specific price should be invented, and no inference should convert a qualitative impression like "cheap" into a specific numerical amount. Pricing contributes to feasibility evaluation and to traveler choice, but the pricing structure itself is simply a recorded experience or provider attribute — it should be represented as known when known, and as unknown when it is not, without filling the gap with an assumption.

---

## 12. Accessibility and Traveler Compatibility

Accessibility information is a supply-side attribute describing whether and how an experience accommodates specific physical or situational needs. Relevant concepts include:

- Documented accessibility characteristics
- Unknown accessibility information
- Physical or situational compatibility
- The relationship between a traveler's accessibility requirements and an experience's accessibility characteristics

A critical distinction applies here: the absence of accessibility information does not mean the experience is accessible. Missing accessibility information should be represented as unknown, not as a positive claim. AI reasoning must not fabricate accessibility claims — describing an experience as accessible, or as compatible with a specific accessibility requirement, requires actual supporting information, not an assumption made in the absence of data.

---

## 13. Location and Spatial Context

Location is a foundational attribute of every experience, with several relevant conceptual dimensions:

- Geographic position
- Destination area
- Proximity to other points of interest
- Neighborhood context
- Relationship to routes
- Relationship to other experiences
- Geographic clustering (how densely experiences are distributed in an area)

Location affects several downstream concerns:

- Traveler convenience (how easy an experience is to reach)
- Travel time (how long it takes to get there)
- Itinerary composition (whether an experience fits well alongside other planned stops)
- Route feasibility (whether movement to and from the experience is realistic)
- Contextual relevance (whether an experience is a reasonable candidate given the traveler's current or planned location)

This document does not describe specific mapping or geocoding implementations; location is treated here purely as a domain-level concept that shapes how an experience relates to a traveler's plan.

---

## 14. Provider Domain

A local provider is the supply-side participant responsible for offering or maintaining one or more experiences. Documented provider types include:

- Restaurant, café, or street-food provider
- Cultural venue
- Tour guide or walking-tour operator
- Workshop or craft studio
- Outdoor activity operator
- Local events organizer

These provider types describe domain roles — the kind of offering a provider is associated with — rather than rigid classifications that fully determine how any given provider behaves. A provider is the entity behind one or more experiences; its role is to offer and maintain those experiences within the ecosystem.

---

## 15. Provider and Experience Relationship

The core relationship is:

PROVIDER
→ OFFERS
→ EXPERIENCE

The experience is what the traveler actually evaluates and potentially visits. The provider is the entity associated with delivering or maintaining that offering. A single provider may have multiple experiences, and a single traveler demand pattern may relate to many different providers across the catalog.

Provider-level information and experience-level information should not be conflated. Consider the difference between:

Provider-level fact: "This provider operates multiple offerings."

Experience-level fact: "This particular offering has a specific operating condition."

A general fact about a provider does not automatically apply identically to every experience that provider offers — each experience can carry its own distinct characteristics and state, even under the same provider.

---

## 16. Provider Operational Context

Several supply-side operational factors may affect whether an experience can actually be delivered:

- Operating conditions
- Resource availability
- Workforce conditions
- Capacity
- Temporary disruption
- Demand pressure
- Experience-specific availability
- Changes caused by real-world conditions

Reasoning about these factors should use cautious language. A provider should not be described as definitely changing its operations because of a weather event or a demand signal unless there is actual evidence that such a change has occurred. It is reasonable to say a provider's operations *may* be affected by a given condition; it is not appropriate to assert that a specific operational change *has* happened without supporting evidence.

---

## 17. Experience State vs Provider State

This distinction must remain explicit throughout reasoning about the supply side.

**Provider state** is the broader condition of the provider or business as a whole.

**Experience state** is the condition of one specific offering associated with that provider.

A provider can remain fully operational while one specific experience it offers is unavailable. A provider can have several experiences simultaneously in different states — one open, one closed, one capacity-limited. These two levels of state must not be collapsed into each other; a fact about the provider's general operation does not automatically tell you the state of any one particular experience, and vice versa.

---

## 18. Provenance and Evidence Quality

Experience intelligence depends heavily on the origin and reliability of the information behind it. Relevant conceptual categories of information source include:

- Authoritative provider information (supplied directly by the entity responsible for the offering)
- Trusted external or catalog information (sourced from an established open-data or licensed catalog)
- Public-source information (broader publicly available information not tied to a specific authoritative party)
- Traveler-contributed information (submitted by travelers themselves)
- Inferred information (derived through reasoning rather than directly observed)
- Missing information (simply not available from any source)

The system should preserve the difference between a **fact from a source** and a **model inference**. A fact carries the weight of its originating source; an inference carries the weight of the reasoning that produced it, which is generally weaker. The more uncertain the source or the interpretation, the more cautiously that information should be used in any downstream reasoning. Traveler-contributed information, in particular, should not be treated as identical in reliability to verified authoritative information — it is a valuable but distinct category of evidence, with its own degree of uncertainty.

---

## 19. Data Completeness and Unknown Values

Incomplete experience records are a normal, expected condition in a real-world local-experience ecosystem, not an anomaly to be corrected by assumption. Attributes that may commonly be missing include:

- Hours
- Ratings
- Reviews
- Capacity
- Availability
- Accessibility
- Pricing
- Environmental characteristics

The governing rule is:

MISSING INFORMATION → UNKNOWN

not:

MISSING INFORMATION → FAVORABLE ASSUMPTION

This is a central safety and trust principle for the entire domain. A missing rating is not a good rating. A missing accessibility note is not a claim of accessibility. A missing price is not a claim of affordability. Preserving "unknown" as its own distinct state, rather than resolving it into a convenient positive assumption, is essential to keeping the system's representations honest.

---

## 20. Experience and Feasibility

The supply side plays a direct role in the deterministic feasibility concept introduced in Document 1. A feasibility decision may depend on known experience attributes such as:

- Time
- Distance
- Operating status
- Availability
- Capacity
- Price
- Accessibility
- Itinerary conflicts

This document does not reproduce the full feasibility framework from Document 1; the relevant supply-side relationship is:

EXPERIENCE DATA
+ TRAVELER CONSTRAINTS
+ CURRENT CONTEXT
→ FEASIBILITY EVALUATION

and:

UNKNOWN REQUIRED EXPERIENCE DATA
→ POSSIBLE UNKNOWN FEASIBILITY

When a fact required for a feasibility evaluation is not actually known about an experience, the resulting feasibility conclusion can itself become uncertain rather than confidently positive or negative — mirroring the UNKNOWN feasibility state from Document 1. AI-level interpretation of experience data does not replace this deterministic feasibility evaluation; it may help understand or summarize the data, but the actual feasibility conclusion remains a deterministic determination.

---

## 21. Experience and Traveler Fit

This section connects the supply side of this document to the traveler-behavior side of Document 3. The conceptual relationship is:

TRAVELER INTENT
+ TRAVELER PREFERENCES
+ TRAVELER CONSTRAINTS
+ EXPERIENCE CHARACTERISTICS
→ MATCH / FIT

Traveler fit is contextual, not intrinsic to the experience alone. The same experience can fit one traveler well and fit another poorly, depending on each traveler's intent, preferences, constraints, and current context. A broad experience category should not be treated as a guarantee of suitability for any given traveler — category membership indicates what kind of experience something is, not that it will automatically satisfy every traveler who expresses interest in that category.

---

## 22. Experience and Weather

This section connects the supply side to Document 2's weather framework, without duplicating it. Environmental conditions interact with experience characteristics in several conceptual ways:

- Outdoor exposure
- Shelter
- Activity intensity
- Sensitivity to precipitation
- Sensitivity to wind
- Sensitivity to heat
- Dependence on movement

The relevant relationship, stated qualitatively and without numerical thresholds, is:

WEATHER
+ EXPERIENCE CHARACTERISTICS
→ POSSIBLE SUITABILITY CHANGE

This document does not restate Document 2's detailed direct/secondary/cascading effect framework, its impact classification categories, or any rainfall, wind, or temperature thresholds. The point relevant here is simply that an experience's own characteristics (how exposed, how sheltered, how weather-sensitive it is) are the input that Document 2's weather-impact reasoning acts upon — this document supplies that input's meaning; Document 2 explains how it is evaluated against changing conditions.

---

## 23. Experience and Route / Movement

An experience cannot be evaluated entirely as an isolated point; how it is reached matters as much as what it is. Relevant concepts include:

- Accessibility by route
- Travel time
- Movement burden
- Distance
- Geographic relation to other stops
- Route conditions
- Weather-sensitive movement

An important relationship to preserve:

EXPERIENCE MAY REMAIN AVAILABLE
while
ROUTE FEASIBILITY CHANGES.

An experience's own operational state (open, available, has capacity) is conceptually distinct from the state of the route leading to it. A perfectly available experience can still become impractical to include in a plan if the movement required to reach it becomes unreliable or excessively burdensome. This document does not describe specific routing implementations; the relevant point is only that experience state and movement state are related but distinct concepts.

---

## 24. Experience and Itinerary Composition

Experiences become components of a multi-stop itinerary through the conceptual relationship:

EXPERIENCES
+ TIMING
+ MOVEMENT
+ CONSTRAINTS
→ ITINERARY

Relevant considerations include:

- Compatibility between stops
- Sequencing
- Duration
- Travel time
- Total budget across the plan
- Operating windows
- Capacity
- Traveler context

This document does not reproduce Document 1's full itinerary and composition framework. The point specific to this document is that itinerary composition depends on accurate, honestly-represented experience-level characteristics as its raw material — an itinerary built from experience data that silently assumes unknown facts to be favorable is not a trustworthy plan, regardless of how well-composed its structure appears.

---

## 25. Experience Changes and Dynamic Adaptation

An experience's state may change after a plan involving it has already been created. Possible causes include:

- Availability changes
- Operating condition changes
- Capacity changes
- Event status changes
- Weather effects
- Provider operational changes
- Traveler context changes

The conceptual flow is:

EXISTING EXPERIENCE STATE
→ CHANGE DETECTED
→ CURRENT PLAN REASSESSED
→ REMAINING ITINERARY EVALUATED
→ ALTERNATIVES MAY BE CONSIDERED

This mirrors the dynamic replanning concept from Document 1 and the weather-driven replanning relationship from Document 2, applied specifically to experience-level state changes. An important caution applies: a simulated or hypothetical possibility (such as a what-if scenario, as described in Document 2) is not automatically a real state change. Only an actual, evidenced change in an experience's recorded state should trigger a real reassessment of a plan.

---

## 26. Events as Experience Objects

Events function as local experiences while carrying additional time-dependent characteristics. Relevant conceptual attributes include:

- Event identity
- Event timing
- Location
- Operating or occurrence status
- Attendance or capacity considerations, where known
- Weather sensitivity
- Cancellation or postponement uncertainty
- Traveler relevance

A critical rule governs event reasoning in this domain:

WEATHER
does NOT automatically mean
EVENT CANCELLED.

Actual event status must come from authoritative available information, not from a weather condition alone, however severe that condition might seem. AI-level reasoning may note that adverse weather makes disruption more plausible for a given event, but it must not fabricate or assert an actual cancellation, postponement, or other status change without real evidence supporting it.

---

## 27. Provider Intelligence and Traveler Demand

This section connects the supply side of this document to the demand-side concepts of Document 3. Two complementary conceptual flows apply:

TRAVELER BEHAVIOR
→ DEMAND SIGNALS
→ PROVIDER INSIGHT

and:

PROVIDER / EXPERIENCE CHARACTERISTICS
→ SUPPLY REPRESENTATION
→ MATCHING

Provider intelligence can conceptually include understanding:

- Who interacts with an experience
- What kinds of traveler demand appear
- When interest occurs
- Which categories attract attention
- How demand changes with context
- Possible supply-demand mismatches

No specific provider statistics are established here, and observed demand should not be assumed to automatically represent true underlying market demand — as Document 3 establishes, individual and aggregate signals both carry their own uncertainty, and what is observed through the system is evidence of demand, not a complete or certain measurement of it.

---

## 28. Supply-Demand Matching

The two-sided matching relationship connects traveler demand and experience supply:

TRAVELER DEMAND
↔
EXPERIENCE SUPPLY

The traveler side may contribute intent, preference, constraints, current context, and behavior (as detailed in Document 3). The supply side may contribute experience characteristics, provider context, availability, operating conditions, capacity, and location (as detailed throughout this document).

Matching means identifying meaningful compatibility between these two sides. It does not guarantee booking, attendance, conversion, satisfaction, or provider acceptance — matching identifies that a candidate connection is worth surfacing, not that any particular outcome will follow from it.

---

## 29. Experience Intelligence and the Digital Twin

Experiences and providers are persistent real-world entities whose state can participate in a broader, continuously evolving system representation — a Digital Twin, as introduced conceptually in Document 2. The conceptual relationship is:

TRAVELERS
+ EXPERIENCES
+ PROVIDERS
+ ROUTES
+ ITINERARIES
+ WEATHER
+ SOCIAL SIGNALS
→ EVOLVING SYSTEM REPRESENTATION

This document contributes the semantic and operational meaning of the experience and provider entities to that larger picture — what they are, what characterizes them, and how their state can change. The implementation-level architecture of how such a system representation is constructed, updated, and simulated belongs to a separate document in this corpus; this document introduces the relationship only at the conceptual level.

---

## 30. Uncertainty in Experience and Provider Reasoning

Reasoning about experiences and providers should distinguish among four categories:

- **KNOWN** — directly recorded or confirmed.
- **INFERRED** — reasonably suggested by a known fact, but not itself directly recorded.
- **UNCERTAIN** — plausible but weakly supported.
- **UNKNOWN** — no meaningful evidence available.

Examples:

Known: "The experience has a recorded operating window."

Unknown: "Current availability is not available."

Inferred: "The experience may be less exposed to rain because its activity is indoors."

Uncertain: "A provider may experience increased demand under the changed conditions."

Inferred information must never be allowed to silently become treated as verified state. An inference remains an inference, however reasonable, and should be labeled and reasoned about accordingly rather than presented with the confidence of a recorded fact.

---

## 31. AI and Domain Intelligence Boundaries

AI or domain intelligence MAY:

- Interpret experience characteristics
- Classify contextual suitability
- Summarize provider or experience information
- Reason about possible fit
- Connect experience attributes with traveler context
- Explain potential environmental effects
- Identify possible supply-demand relationships
- Summarize uncertainty
- Explain why an experience may or may not align with a request

AI or domain intelligence MUST NOT:

- Invent experience attributes
- Invent opening hours
- Invent availability
- Invent capacity
- Invent prices
- Invent accessibility claims
- Invent provider operations
- Claim an event is cancelled without evidence
- Fabricate ratings or reviews
- Fabricate demand statistics
- Override deterministic feasibility
- Silently treat unknown fields as positive facts
- Mutate real system state based solely on an inference

Deterministic/backend systems remain authoritative for:

- Actual experience records
- Actual provider records
- Actual availability
- Actual operating status
- Actual capacity
- Actual prices when stored
- Actual route calculations
- Actual feasibility
- Actual itinerary state
- Actual booking/request state
- Actual database mutations

---

## 32. Conceptual Supply-Side Examples

**Example A.**
A traveler requests a cultural indoor experience. The experience category and characteristics match, but current operating status is unknown. The system must preserve the uncertainty rather than assuming it is open.

**Example B.**
A provider has multiple experiences. One experience becomes unavailable while another remains available. The provider remains operational, but experience-level state differs between the two offerings.

**Example C.**
An outdoor experience is normally suitable. Weather changes. The experience itself still exists, but its contextual suitability may decrease as a result.

**Example D.**
A traveler wants an experience under a maximum budget. The experience is relevant but its price is unknown. The system cannot treat the unknown price as automatically affordable.

**Example E.**
An event is scheduled during adverse weather. The weather suggests possible disruption, but the actual cancellation status remains unknown until it is verified through authoritative information.

**Example F.**
Several travelers show increased interest in a category. That may create a demand signal, but it does not prove that every traveler prefers that category.

**Example G.**
A route to an experience becomes problematic while the experience itself remains operational. The issue is movement feasibility, not necessarily experience availability.

All examples above are generic illustrations. No real businesses, statistics, traveler datasets, or unsupported locations are represented.

---

## 33. Domain Relationships Summary

**Supply entity chain:**

PROVIDER
→ OFFERS
→ EXPERIENCE
→ HAS CHARACTERISTICS
→ HAS OPERATIONAL STATE
→ EXISTS AT LOCATION
→ CAN BE PART OF ITINERARY

A provider offers one or more experiences; each experience carries its own characteristics and operational state, exists at a specific location, and can potentially become part of a traveler's itinerary.

**Traveler fit chain:**

TRAVELER CONTEXT
+ EXPERIENCE CHARACTERISTICS
+ CURRENT CONDITIONS
→ CONTEXTUAL FIT

A traveler's context, combined with an experience's characteristics and the current conditions surrounding both, determines how well that experience fits that traveler right now.

**Feasibility chain:**

EXPERIENCE FACTS
+ TRAVELER CONSTRAINTS
+ ROUTES / TIMING
→ DETERMINISTIC FEASIBILITY

Known experience facts, combined with the traveler's constraints and the routing and timing involved, feed into a deterministic feasibility evaluation, with unknown required facts producing uncertainty rather than an assumed favorable outcome.

**Supply-demand chain:**

TRAVELER BEHAVIOR
→ DEMAND SIGNAL
→ PROVIDER INTELLIGENCE

Observed traveler behavior around experiences generates demand signals, which aggregate into provider-facing intelligence about interest and fit.

**Adaptation chain:**

REAL-WORLD CHANGE
→ EXPERIENCE / PROVIDER STATE CHANGE
→ REASSESSMENT
→ POSSIBLE REPLANNING

A real-world change (in weather, operations, availability, or other conditions) can alter an experience's or provider's actual state, which can trigger reassessment of an existing plan and, where necessary, replanning.

---

## 34. Domain Vocabulary

**Local Experience** — A real-world activity, place, venue, event, or local offering that a traveler can discover and potentially include in a plan; the core discoverable unit of the LocaLens domain.

**Experience** — Synonymous with Local Experience.

**Experience Characteristic** — A specific attribute describing an experience (such as category, location, price, or environmental type).

**Experience Category** — One of the twenty labels in the current LocaLens taxonomy classifying what kind of experience an offering represents.

**Provider** — The person or business responsible for offering or maintaining one or more experiences.

**Provider Offering** — An experience associated with a specific provider.

**Experience State** — The current operational condition of one specific experience (such as available, unavailable, or capacity-limited).

**Provider State** — The broader operational condition of a provider as a whole, distinct from any one experience's state.

**Availability** — Whether an experience can actually be used, distinguished from mere existence, open status, or capacity.

**Operating Condition** — Information about when and whether an experience is scheduled to run.

**Capacity** — The participant or resource limit associated with an experience at a given time.

**Pricing** — The cost information associated with an experience or provider offering.

**Accessibility Information** — Documented characteristics describing how an experience accommodates specific physical or situational needs.

**Experience Suitability** — The degree to which an experience's characteristics fit a traveler and current context.

**Contextual Fit** — The specific, situational match between a traveler and an experience at a given moment, as distinct from the experience's intrinsic characteristics.

**Experience Provenance** — The origin and reliability category of the information describing an experience (authoritative, catalog, public, traveler-contributed, inferred, or missing).

**Evidence Quality** — The degree of confidence warranted by a given piece of information, based on its provenance.

**Known** — Directly recorded or confirmed information.

**Inferred** — A conclusion reasonably suggested by known facts, but not itself a directly recorded fact.

**Uncertain** — Plausible but weakly supported information.

**Unknown** — Information for which no meaningful evidence is available.

**Experience Demand** — The pattern of traveler interest directed toward a specific experience or category.

**Supply** — The aggregate of experiences and their characteristics offered by providers within the ecosystem.

**Traveler–Provider Matching** — The conceptual process of identifying meaningful compatibility between traveler demand and provider supply.

**Operational State** — General term for the current condition (of an experience or a provider) that determines whether and how it can currently function.

**Event Experience** — An experience with event-like, time-dependent characteristics, such as a scheduled occurrence and occupancy considerations.

**Route Accessibility** — The practical ease or difficulty of reaching an experience via a given route, distinct from the experience's own operational state.

**Experience Feasibility** — The evaluation of whether a specific experience satisfies the constraints required for a traveler's plan, drawing on experience-level facts.

**Digital Twin Entity** — Any persistent real-world entity (such as an experience or provider) whose state can participate in an evolving system representation.

---

## 35. AI-System Boundaries

AI may interpret. AI may summarize. AI may reason about contextual relationships. AI may explain possible suitability.

But:

AI does NOT create facts.

AI does NOT become the source of truth for experience or provider state.

AI does NOT replace deterministic feasibility.

AI does NOT turn missing data into positive assumptions.

AI does NOT fabricate provider actions, availability, or event status.

AI does NOT modify actual system state merely because a scenario appears likely.

The final authority for real-world state remains the deterministic/backend system and its available evidence. AI-level reasoning about experiences and providers exists to assist understanding, interpretation, and explanation — never to substitute for actual, evidenced system state.

---

*Source note: This document was derived from the LocaLens project's product, architecture, and current implementation documentation (experience taxonomy, provenance, operational status, and provider concepts), together with Documents 1–3 of this alignment corpus, for the purpose of domain-alignment corpus creation. It describes stable conceptual relationships and does not represent a specific implementation status at any point in time.*
