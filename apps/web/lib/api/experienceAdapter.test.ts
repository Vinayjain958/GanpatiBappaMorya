import { describe, expect, it } from "vitest";
import { mapApiExperienceToUi } from "./experienceAdapter";
import type { ApiExperienceSummary } from "@/types/api";

function makeApiExperience(overrides: Partial<ApiExperienceSummary> = {}): ApiExperienceSummary {
  return {
    id: "exp-1",
    title: "Grand Heritage Museum",
    short_description: "A museum.",
    category: { id: "cat-1", slug: "museums", name: "Museums", icon: null },
    location: {
      id: "loc-1",
      latitude: 18.93,
      longitude: 72.83,
      place_name: "Grand Heritage Museum",
      address: null,
      locality: "Fort",
      city: "Mumbai",
      state: null,
      country: "India",
    },
    provider: {
      id: "prov-1",
      business_name: "Grand Heritage Museum",
      provider_type: null,
      verification_status: "catalog_imported",
      is_synthetic: false,
    },
    currency: "INR",
    price: null,
    minimum_price: null,
    maximum_price: null,
    price_type: "unknown",
    is_price_estimated: false,
    duration_minutes: null,
    duration_is_estimated: false,
    rating: null,
    review_count: null,
    status: "active",
    verification_status: "unverified",
    is_synthetic: false,
    is_enriched: false,
    image: null,
    distance_km: null,
    travel_time_minutes: null,
    travel_time_source: null,
    ...overrides,
  };
}

describe("mapApiExperienceToUi — image resolution", () => {
  it("uses the resolved Wikimedia image when present", () => {
    const api = makeApiExperience({
      image: {
        url: "https://upload.wikimedia.org/wikipedia/commons/example.jpg",
        thumbnail_url: "https://thumb.wikimedia.org/example_thumb.jpg",
        source: "wikimedia_commons",
        source_url: "https://commons.wikimedia.org/wiki/File:Example.jpg",
        license: "CC BY-SA 4.0",
        license_url: "https://creativecommons.org/licenses/by-sa/4.0",
        author: "Jane Doe",
        attribution_text: "Photo: Wikimedia Commons · Author: Jane Doe · License: CC BY-SA 4.0",
        is_place_specific: true,
        is_synthetic: false,
        match_method: "exact_title",
      },
    });

    const ui = mapApiExperienceToUi(api, null);

    expect(ui.imageUrl).toBe("https://upload.wikimedia.org/wikipedia/commons/example.jpg");
    expect(ui.image.isFallback).toBe(false);
    expect(ui.image.isPlaceSpecific).toBe(true);
    expect(ui.image.author).toBe("Jane Doe");
    expect(ui.image.license).toBe("CC BY-SA 4.0");
    expect(ui.image.attributionText).toContain("Jane Doe");
  });

  it("falls back to category art when no image was resolved, never fabricating a photo", () => {
    const api = makeApiExperience({ image: null, category: { id: "cat-2", slug: "museums", name: "Museums", icon: null } });

    const ui = mapApiExperienceToUi(api, null);

    expect(ui.image.isFallback).toBe(true);
    expect(ui.image.isPlaceSpecific).toBe(false);
    expect(ui.image.attributionText).toBeNull();
    expect(ui.imageUrl).toMatch(/^https:\/\//); // still a valid, renderable URL
  });

  it("marks a semantic-fallback Wikimedia image as not place-specific", () => {
    const api = makeApiExperience({
      image: {
        url: "https://upload.wikimedia.org/wikipedia/commons/generic-museum.jpg",
        thumbnail_url: "https://thumb.wikimedia.org/generic-museum_thumb.jpg",
        source: "wikimedia_commons",
        source_url: "https://commons.wikimedia.org/wiki/File:Generic_museum.jpg",
        license: "CC0",
        license_url: null,
        author: null,
        attribution_text: "Photo: Wikimedia Commons · License: CC0",
        is_place_specific: false,
        is_synthetic: false,
        match_method: "semantic_fallback",
      },
    });

    const ui = mapApiExperienceToUi(api, null);

    expect(ui.image.isFallback).toBe(false); // it IS a real Wikimedia image
    expect(ui.image.isPlaceSpecific).toBe(false); // but not verified as this exact venue
  });

  it("never marks the category fallback image as synthetic Wikimedia content", () => {
    const api = makeApiExperience({ image: null });

    const ui = mapApiExperienceToUi(api, null);

    expect(ui.image.source).toBeNull();
  });
});
