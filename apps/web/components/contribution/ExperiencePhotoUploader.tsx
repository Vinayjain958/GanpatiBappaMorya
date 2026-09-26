"use client";

import { useRef, useState } from "react";
import { Camera, ImagePlus, X } from "lucide-react";
import { Button } from "@/components/ui/Button";

const ACCEPTED_TYPES = "image/jpeg,image/png,image/webp";

/**
 * Photo-first upload for the traveler contribution flow (spec §10/§54).
 * Two separate file inputs: one with `capture="environment"` so mobile
 * browsers open the rear camera directly, one plain picker for the
 * gallery/desktop file dialog. Client-side type/size checks here are a
 * UX nicety only — the server (services/media_validation.py) is the
 * authoritative check and re-validates real file content regardless of
 * what the browser reports.
 */
export function ExperiencePhotoUploader({
  file,
  onChange,
  maxBytes = 8 * 1024 * 1024,
}: {
  file: File | null;
  onChange: (file: File | null) => void;
  maxBytes?: number;
}) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);

  function handlePick(selected: File | undefined) {
    setWarning(null);
    if (!selected) return;

    if (!["image/jpeg", "image/png", "image/webp"].includes(selected.type)) {
      setWarning("Please choose a JPG, PNG, or WebP image.");
      return;
    }
    if (selected.size > maxBytes) {
      setWarning("That photo is too large — please choose a smaller one.");
      return;
    }

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(selected));
    onChange(selected);
  }

  function clear() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setWarning(null);
    onChange(null);
    if (cameraInputRef.current) cameraInputRef.current.value = "";
    if (galleryInputRef.current) galleryInputRef.current.value = "";
  }

  if (file && previewUrl) {
    return (
      <div className="space-y-2">
        <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl bg-surface-sunken">
          {/* eslint-disable-next-line @next/next/no-img-element -- local object URL preview, next/image needs a served URL */}
          <img src={previewUrl} alt="" className="size-full object-cover" />
          <button
            type="button"
            onClick={clear}
            aria-label="Remove photo"
            className="absolute right-3 top-3 inline-flex size-9 items-center justify-center rounded-full bg-surface/90 text-ink shadow-sm backdrop-blur hover:bg-danger-soft hover:text-danger"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button type="button" variant="outline" onClick={() => cameraInputRef.current?.click()} className="flex-1">
          <Camera className="size-4" aria-hidden="true" />
          Take Photo
        </Button>
        <Button type="button" variant="outline" onClick={() => galleryInputRef.current?.click()} className="flex-1">
          <ImagePlus className="size-4" aria-hidden="true" />
          Choose from Gallery
        </Button>
      </div>

      {/* Rear camera on supporting mobile browsers; falls back to a
          normal file picker everywhere else. */}
      <input
        ref={cameraInputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        capture="environment"
        className="sr-only"
        onChange={(event) => handlePick(event.target.files?.[0])}
      />
      <input
        ref={galleryInputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        className="sr-only"
        onChange={(event) => handlePick(event.target.files?.[0])}
      />

      {warning ? <p className="text-xs text-danger">{warning}</p> : null}
    </div>
  );
}
