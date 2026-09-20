import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";

/** Wordmark: a monogram "P" whose counter carries the amber citation dot. */
export function Logo({ className }: { className?: string }) {
  return (
    <Link to="/" className={cn("inline-flex items-center gap-2 rounded-md", className)} aria-label="PortfolioAI home">
      <svg viewBox="0 0 32 32" className="size-7" aria-hidden="true">
        <rect width="32" height="32" rx="8" className="fill-primary" />
        <path
          d="M9 22V10h7a4 4 0 0 1 0 8h-4"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-primary-foreground"
        />
        <circle cx="23" cy="10" r="2.4" className="fill-citation" />
      </svg>
      <span className="font-heading text-lg font-semibold tracking-tight">PortfolioAI</span>
    </Link>
  );
}
