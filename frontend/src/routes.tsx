import type { RouteObject } from "react-router-dom";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PublicLayout } from "@/components/layout/PublicLayout";
import Evaluation from "@/pages/admin/Evaluation";
import JobAnalyzer from "@/pages/admin/JobAnalyzer";
import Overview from "@/pages/admin/Overview";
import NotFound from "@/pages/NotFound";
import Home from "@/pages/public/Home";
import { About, Certifications, Chat, Contact, Experience, Projects, Skills } from "@/pages/public/PublicPages";

export const routes: RouteObject[] = [
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <Home /> },
      { path: "/about", element: <About /> },
      { path: "/projects", element: <Projects /> },
      { path: "/skills", element: <Skills /> },
      { path: "/experience", element: <Experience /> },
      { path: "/certifications", element: <Certifications /> },
      { path: "/contact", element: <Contact /> },
      { path: "/chat", element: <Chat /> },
    ],
  },
  {
    // Owner-only screens. A route guard is added together with authentication (phase 3).
    element: <DashboardLayout />,
    children: [
      { path: "/admin", element: <Overview /> },
      { path: "/job-analyzer", element: <JobAnalyzer /> },
      { path: "/evaluation", element: <Evaluation /> },
    ],
  },
  { path: "*", element: <NotFound /> },
];
