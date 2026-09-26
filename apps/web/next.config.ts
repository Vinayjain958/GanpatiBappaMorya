import type { NextConfig } from "next";

// The API's own origin, so next/image can load traveler-uploaded photos
// served from its /media static mount (see apps/api/src/core/app.py and
// docs/DECISIONS.md ADR-058) — defaults to the local dev API port.
const apiOrigin = new URL(process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000");

// The dev API is typically localhost/a private IP, which next/image's
// optimizer refuses to fetch by default as an SSRF guard. Only opt out of
// that guard when the configured API origin is actually a loopback/private
// address (i.e. local development) — a real deployed API origin is a public
// hostname and never needs this, so production is never silently exposed.
const isLocalApiOrigin = ["localhost", "127.0.0.1", "::1"].includes(apiOrigin.hostname);

const nextConfig: NextConfig = {
  images: {
    ...(isLocalApiOrigin ? { dangerouslyAllowLocalIP: true } : {}),
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "upload.wikimedia.org",
      },
      {
        protocol: "https",
        hostname: "*.wikimedia.org",
      },
      {
        protocol: apiOrigin.protocol.replace(":", "") as "http" | "https",
        hostname: apiOrigin.hostname,
        port: apiOrigin.port,
      },
    ],
  },
};

export default nextConfig;
