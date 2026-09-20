import { PhasePage } from "@/components/common/PhasePage";

export function About() {
  return (
    <PhasePage
      phase={5}
      title="About"
      description="Who the portfolio belongs to and what they are working towards."
      features={["Bio, title and location from the profile", "Education timeline", "Achievements"]}
    />
  );
}

export function Projects() {
  return (
    <PhasePage
      phase={5}
      title="Projects"
      description="Things built, the problem each one solves, and the tools behind it."
      features={[
        "Project cards with technologies and links",
        "Detail view with problem statement, features and role",
        "Filter by technology",
      ]}
    />
  );
}

export function Skills() {
  return (
    <PhasePage
      phase={5}
      title="Skills"
      description="Technical skills grouped by category, with proficiency."
      features={["Skills grouped by category", "Proficiency level and years of experience"]}
    />
  );
}

export function Experience() {
  return (
    <PhasePage
      phase={5}
      title="Experience"
      description="Internships and work, with what was delivered."
      features={["Timeline of roles", "Skills used and achievements per role"]}
    />
  );
}

export function Certifications() {
  return (
    <PhasePage
      phase={5}
      title="Certifications"
      description="Courses and credentials, with links to verify them."
      features={["Certificate list with issuer and date", "Credential links"]}
    />
  );
}

export function Contact() {
  return (
    <PhasePage
      phase={5}
      title="Contact"
      description="Ways to get in touch."
      features={["Email, phone, LinkedIn and GitHub from the profile", "Contact form"]}
    />
  );
}

export function Chat() {
  return (
    <PhasePage
      phase={8}
      title="Ask the portfolio"
      description="A chat assistant that answers from the portfolio and cites its sources."
      features={[
        "Streaming answers with source citations",
        "Conversation history and new conversation",
        "Copy, regenerate and clear",
      ]}
    />
  );
}
