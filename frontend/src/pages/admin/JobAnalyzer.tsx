import { PhasePage } from "@/components/common/PhasePage";

export default function JobAnalyzer() {
  return (
    <PhasePage
      phase={9}
      title="Job analyzer"
      description="Paste a job description and see how the profile matches it."
      features={[
        "Required and preferred skills extracted from the description",
        "Matching skills, skill gaps, relevant projects and experience",
        "Improvement suggestions based only on what is actually in the profile",
        "Resume comparison with missing keywords and ATS observations",
      ]}
    />
  );
}
