import { CircleDashed } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ROADMAP } from "@/lib/roadmap";

interface PhaseNoticeProps {
  /** The build phase in which this feature is implemented (see lib/roadmap.ts). */
  phase: number;
  /** What the finished feature will contain. */
  features: string[];
  className?: string;
}

/** Card explaining that a feature lands in a later build phase, and what it will include. */
export function PhaseNotice({ phase, features, className }: PhaseNoticeProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CircleDashed className="size-4 text-muted-foreground" aria-hidden="true" />
          Built in phase {phase}: {ROADMAP[phase]}
        </CardTitle>
        <CardDescription>This will include:</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="list-disc space-y-1.5 pl-5 text-sm">
          {features.map((feature) => (
            <li key={feature}>{feature}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
