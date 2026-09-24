"use client";

import { useEffect, useRef, useState } from "react";
import {
  AttributionControl,
  GeoJSONSource,
  Map as MapLibreMap,
  MapLayerMouseEvent,
  NavigationControl,
  Popup,
  setWorkerUrl,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { RefreshCw } from "lucide-react";
import { mapConfig } from "@/lib/config/map";
import { cn } from "@/lib/utils/cn";
import type { ExperienceFeatureCollection } from "@/lib/geo/geojson";

const SOURCE_ID = "experiences";
const CLUSTER_LAYER = "experience-clusters";
const CLUSTER_COUNT_LAYER = "experience-cluster-count";
const POINT_LAYER = "experience-points";
const ORIGIN_SOURCE_ID = "map-origin";
const ORIGIN_LAYER = "map-origin-point";
const ROUTE_SOURCE_ID = "map-route";
const ROUTE_LAYER = "map-route-line";

const EMPTY_COLLECTION: ExperienceFeatureCollection = { type: "FeatureCollection", features: [] };

// MapLibre GL v6 loads its render worker via `import.meta.url`-relative
// resolution, which Turbopack's dev server doesn't serve as a valid
// module route (404 -> HTML -> "non-JavaScript MIME type" console error).
// Point it at a static copy in public/ instead, which Next.js always
// serves verbatim regardless of bundler — same pattern as
// public/worklets/ for the audio capture worklet. Set once, before any
// Map is constructed.
//
// IMPORTANT: maplibre-gl-worker.mjs itself `import`s a sibling
// maplibre-gl-shared.mjs (both from node_modules/maplibre-gl/dist/) —
// both files must be copied into public/maplibre/ together and kept in
// sync on every maplibre-gl version bump, or the worker's own module
// import 404s inside the worker thread. That failure is silent: the map
// still constructs, controls still render, and dataloading/
// sourcedataloading events keep firing optimistically from the main
// thread forever, but zero real tile network requests ever go out,
// because the fetch logic lives entirely in the (dead) worker.
setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

export interface MapSurfaceProps {
  /** Selection state is encoded in `features` (each feature's
   * `properties.selected`, see lib/geo/geojson.ts) rather than passed
   * separately — the caller marks the selected id when building the
   * FeatureCollection. */
  features?: ExperienceFeatureCollection;
  onSelectFeature?: (id: string) => void;
  origin?: { lat: number; lng: number } | null;
  routeGeometry?: GeoJSON.LineString | null;
  onSearchThisArea?: (bounds: { minLat: number; maxLat: number; minLng: number; maxLng: number }) => void;
  center?: { lat: number; lng: number };
  zoom?: number;
  className?: string;
  label?: string;
}

/**
 * Real MapLibre GL JS map surface (Phase 4) — replaces the Phase 1
 * placeholder. Renders catalog experiences as a clustered GeoJSON source
 * rather than one DOM marker per result. Style URL comes from
 * lib/config/map.ts, never hardcoded here.
 */
export function MapSurface({
  features = EMPTY_COLLECTION,
  onSelectFeature,
  origin = null,
  routeGeometry = null,
  onSearchThisArea,
  center,
  zoom,
  className,
  label = "Experience map",
}: MapSurfaceProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const popupRef = useRef<Popup | null>(null);
  const [mapError, setMapError] = useState(false);
  const [showSearchArea, setShowSearchArea] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Initialize once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let map: MapLibreMap;
    try {
      map = new MapLibreMap({
        container: containerRef.current,
        style: mapConfig.styleUrl,
        center: [
          center?.lng ?? mapConfig.defaultCenter.lng,
          center?.lat ?? mapConfig.defaultCenter.lat,
        ],
        zoom: zoom ?? mapConfig.defaultZoom,
        maxZoom: mapConfig.maxZoom,
        minZoom: mapConfig.minZoom,
        attributionControl: false,
      });
    } catch {
      // Deferred so this isn't a direct synchronous setState call inside
      // the effect body (react-hooks/set-state-in-effect).
      queueMicrotask(() => setMapError(true));
      return;
    }

    mapRef.current = map;

    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    map.addControl(
      new AttributionControl({ customAttribution: mapConfig.attributionHtml, compact: true }),
      "bottom-right",
    );

    map.on("error", () => setMapError(true));

    map.on("load", () => {
      map.addSource(SOURCE_ID, {
        type: "geojson",
        data: EMPTY_COLLECTION,
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 45,
      });

      map.addLayer({
        id: CLUSTER_LAYER,
        type: "circle",
        source: SOURCE_ID,
        filter: ["has", "point_count"],
        paint: {
          "circle-color": "#123a75",
          "circle-radius": ["step", ["get", "point_count"], 16, 10, 20, 25, 26],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });
      map.addLayer({
        id: CLUSTER_COUNT_LAYER,
        type: "symbol",
        source: SOURCE_ID,
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-size": 12,
          "text-font": ["Noto Sans Bold"],
        },
        paint: { "text-color": "#ffffff" },
      });
      map.addLayer({
        id: POINT_LAYER,
        type: "circle",
        source: SOURCE_ID,
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-radius": ["case", ["get", "selected"], 9, 6],
          "circle-color": ["case", ["get", "selected"], "#0ea5c4", "#123a75"],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      map.addSource(ORIGIN_SOURCE_ID, { type: "geojson", data: EMPTY_COLLECTION });
      map.addLayer({
        id: ORIGIN_LAYER,
        type: "circle",
        source: ORIGIN_SOURCE_ID,
        paint: {
          "circle-radius": 8,
          "circle-color": "#e2812c",
          "circle-stroke-width": 3,
          "circle-stroke-color": "#ffffff",
        },
      });

      map.addSource(ROUTE_SOURCE_ID, { type: "geojson", data: EMPTY_COLLECTION });
      map.addLayer({
        id: ROUTE_LAYER,
        type: "line",
        source: ROUTE_SOURCE_ID,
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#0ea5c4", "line-width": 4, "line-opacity": 0.85 },
      });

      map.on("click", CLUSTER_LAYER, (e: MapLayerMouseEvent) => {
        const clusterFeatures = map.queryRenderedFeatures(e.point, { layers: [CLUSTER_LAYER] });
        const clusterId = clusterFeatures[0]?.properties?.cluster_id;
        const source = map.getSource(SOURCE_ID) as GeoJSONSource;
        if (clusterId == null) return;
        source.getClusterExpansionZoom(clusterId).then((targetZoom: number) => {
          const geometry = clusterFeatures[0].geometry;
          if (geometry.type !== "Point") return;
          map[prefersReducedMotion ? "jumpTo" : "easeTo"]({
            center: geometry.coordinates as [number, number],
            zoom: targetZoom,
          });
        });
      });

      map.on("click", POINT_LAYER, (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature || feature.geometry.type !== "Point") return;
        const props = feature.properties as { id: string; title: string; categoryLabel: string; price: number; isSynthetic: boolean };
        onSelectFeature?.(props.id);

        popupRef.current?.remove();
        const coordinates = feature.geometry.coordinates.slice() as [number, number];
        popupRef.current = new Popup({ closeButton: true, offset: 12 })
          .setLngLat(coordinates)
          .setHTML(
            `<div style="font-family:inherit;min-width:160px">
              <p style="margin:0 0 2px;font-size:12px;color:#7c8598;">${props.categoryLabel}</p>
              <p style="margin:0 0 4px;font-weight:600;font-size:13px;">${props.title}</p>
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
                <span style="font-size:12px;color:#4b5567;">${props.isSynthetic ? "LocaLens demo" : "Open data"}</span>
                <span style="font-weight:600;font-size:13px;">${props.price ? `₹${props.price}` : "Free"}</span>
              </div>
              <a href="/discover/${props.id}" style="display:block;margin-top:8px;font-size:12px;font-weight:600;color:#0ea5c4;">View experience →</a>
            </div>`,
          )
          .addTo(map);
      });

      map.on("mouseenter", POINT_LAYER, () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", POINT_LAYER, () => (map.getCanvas().style.cursor = ""));
      map.on("mouseenter", CLUSTER_LAYER, () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", CLUSTER_LAYER, () => (map.getCanvas().style.cursor = ""));

      setLoaded(true);
    });

    if (onSearchThisArea) {
      map.on("dragend", () => setShowSearchArea(true));
      map.on("zoomend", () => setShowSearchArea(true));
    }

    return () => {
      popupRef.current?.remove();
      map.remove();
      mapRef.current = null;
    };
    // Intentionally initialize only once; prop-driven updates happen in
    // the effects below rather than re-creating the map instance.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep the experience source in sync with fresh results.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded) return;
    const source = map.getSource(SOURCE_ID) as GeoJSONSource | undefined;
    source?.setData(features);
  }, [features, loaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded) return;
    const source = map.getSource(ORIGIN_SOURCE_ID) as GeoJSONSource | undefined;
    if (!source) return;
    source.setData(
      origin
        ? {
            type: "FeatureCollection",
            features: [
              { type: "Feature", geometry: { type: "Point", coordinates: [origin.lng, origin.lat] }, properties: {} },
            ],
          }
        : EMPTY_COLLECTION,
    );
  }, [origin, loaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded) return;
    const source = map.getSource(ROUTE_SOURCE_ID) as GeoJSONSource | undefined;
    if (!source) return;
    source.setData(
      routeGeometry
        ? { type: "FeatureCollection", features: [{ type: "Feature", geometry: routeGeometry, properties: {} }] }
        : EMPTY_COLLECTION,
    );
  }, [routeGeometry, loaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded || !center) return;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    map[prefersReducedMotion ? "jumpTo" : "easeTo"]({ center: [center.lng, center.lat], zoom });
    // Only re-center when the caller explicitly changes center/zoom.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center?.lat, center?.lng, loaded]);

  function handleSearchThisArea() {
    const map = mapRef.current;
    if (!map || !onSearchThisArea) return;
    const bounds = map.getBounds();
    onSearchThisArea({
      minLat: bounds.getSouth(),
      maxLat: bounds.getNorth(),
      minLng: bounds.getWest(),
      maxLng: bounds.getEast(),
    });
    setShowSearchArea(false);
  }

  if (mapError) {
    return (
      <div
        role="status"
        className={cn(
          "flex min-h-64 w-full flex-col items-center justify-center gap-2 rounded-xl border border-line bg-surface-sunken text-sm text-ink-muted",
          className,
        )}
      >
        <p>Map temporarily unavailable.</p>
        <p className="text-xs text-ink-subtle">The experience list below still works.</p>
      </div>
    );
  }

  return (
    <div
      className={cn("relative min-h-64 w-full overflow-hidden rounded-xl border border-line", className)}
    >
      <div ref={containerRef} role="img" aria-label={label} className="h-full w-full" />
      {showSearchArea ? (
        <div className="absolute left-1/2 top-3 -translate-x-1/2">
          <button
            type="button"
            onClick={handleSearchThisArea}
            className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3.5 py-1.5 text-xs font-semibold text-ink shadow-md hover:bg-surface-sunken"
          >
            <RefreshCw className="size-3.5" aria-hidden="true" />
            Search this area
          </button>
        </div>
      ) : null}
    </div>
  );
}
