import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { ThemeProvider } from "@/hooks/useTheme";
import { routes } from "@/routes";

/** Render the real route table at a given URL, with all app providers. */
export function renderApp(initialPath = "/") {
  const router = createMemoryRouter(routes, { initialEntries: [initialPath] });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export const healthyPayload = {
  status: "ok",
  app: "PortfolioAI",
  version: "0.1.0",
  environment: "development",
  database: { status: "up", latency_ms: 3.2, detail: null },
  llm_provider: "gemini",
  llm_configured: false,
  vector_store: "pgvector",
  timestamp: "2026-01-01T00:00:00Z",
};
