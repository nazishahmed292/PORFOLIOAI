export interface NavItem {
  label: string;
  to: string;
}

/** Links shown in the public site header. */
export const PUBLIC_NAV: NavItem[] = [
  { label: "About", to: "/about" },
  { label: "Projects", to: "/projects" },
  { label: "Skills", to: "/skills" },
  { label: "Experience", to: "/experience" },
  { label: "Certifications", to: "/certifications" },
  { label: "Contact", to: "/contact" },
];

/** Sections available to the portfolio owner. Grows as admin modules are built. */
export const ADMIN_NAV: NavItem[] = [
  { label: "Overview", to: "/admin" },
  { label: "Job analyzer", to: "/job-analyzer" },
  { label: "RAG evaluation", to: "/evaluation" },
];
