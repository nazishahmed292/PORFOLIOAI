import { PageHeader } from "@/components/common/PageHeader";
import { PhaseNotice } from "@/components/common/PhaseNotice";

interface PhasePageProps {
  title: string;
  description: string;
  phase: number;
  features: string[];
}

/**
 * Route shell for a screen that is built in a later phase. The route, layout and
 * navigation already work, so later phases only replace the body of the page.
 */
export function PhasePage({ title, description, phase, features }: PhasePageProps) {
  return (
    <div className="space-y-8">
      <PageHeader title={title} description={description} />
      <PhaseNotice phase={phase} features={features} className="max-w-2xl" />
    </div>
  );
}
