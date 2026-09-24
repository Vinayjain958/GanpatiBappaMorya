import Link from "next/link";
import { ShieldAlert } from "lucide-react";

export function EmergencyButton() {
  return (
    <Link
      href="/safety/emergency"
      className="flex items-center justify-center gap-2 rounded-xl bg-danger px-5 py-4 text-base font-semibold text-white shadow-sm transition-colors hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-danger"
    >
      <ShieldAlert className="size-5" aria-hidden="true" />
      Emergency help
    </Link>
  );
}
