import type { LucideIcon } from "lucide-react";
import { Compass, MapPinned, Bookmark, ShieldAlert, Store } from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const primaryNav: NavItem[] = [
  { label: "Discover", href: "/discover", icon: Compass },
  { label: "Trips", href: "/trip", icon: MapPinned },
  { label: "Saved", href: "/saved", icon: Bookmark },
  { label: "Safety", href: "/safety", icon: ShieldAlert },
  { label: "Provider", href: "/provider", icon: Store },
];
