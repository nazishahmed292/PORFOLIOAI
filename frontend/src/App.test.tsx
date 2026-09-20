import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { healthyPayload, jsonResponse, renderApp } from "@/test/utils";

describe("public site", () => {
  it("renders the landing page with an example cited answer", () => {
    renderApp("/");
    expect(screen.getByRole("heading", { level: 1, name: /ask this portfolio anything/i })).toBeInTheDocument();
    const example = screen.getByRole("figure", { name: /example conversation/i });
    const sources = within(example).getAllByRole("listitem");
    expect(sources).toHaveLength(3);
    expect(sources[0]).toHaveTextContent("Code Plagiarism Pattern Detector");
  });

  it.each([
    ["/about", "About"],
    ["/projects", "Projects"],
    ["/skills", "Skills"],
    ["/experience", "Experience"],
    ["/certifications", "Certifications"],
    ["/contact", "Contact"],
    ["/chat", "Ask the portfolio"],
  ])("routes %s to its page", (path, heading) => {
    renderApp(path);
    expect(screen.getByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
  });

  it("shows a 404 page for unknown routes", () => {
    renderApp("/no-such-page");
    expect(screen.getByRole("heading", { name: /this page doesn't exist/i })).toBeInTheDocument();
  });

  it("navigates between pages from the header", async () => {
    renderApp("/");
    const nav = screen.getByRole("navigation", { name: "Main" });
    await userEvent.click(within(nav).getByRole("link", { name: "Projects" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Projects" })).toBeInTheDocument();
  });

  it("opens and closes the mobile menu", async () => {
    renderApp("/");
    const toggle = screen.getByRole("button", { name: "Open menu" });
    await userEvent.click(toggle);
    expect(screen.getByRole("navigation", { name: "Mobile" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Close menu" }));
    expect(screen.queryByRole("navigation", { name: "Mobile" })).not.toBeInTheDocument();
  });

  it("toggles the dark theme and remembers it", async () => {
    renderApp("/");
    await userEvent.click(screen.getByRole("button", { name: /switch to dark theme/i }));
    expect(document.documentElement).toHaveClass("dark");
    expect(localStorage.getItem("portfolioai-theme")).toBe("dark");
    await userEvent.click(screen.getByRole("button", { name: /switch to light theme/i }));
    expect(document.documentElement).not.toHaveClass("dark");
  });
});

describe("owner dashboard", () => {
  it("shows live system status from the API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(healthyPayload)));
    renderApp("/admin");

    expect(await screen.findByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("3.2 ms")).toBeInTheDocument();
    expect(screen.getByText("pgvector")).toBeInTheDocument();
    expect(screen.getByText("No API key")).toBeInTheDocument();
  });

  it("shows a degraded state when the database is down", async () => {
    const degraded = {
      ...healthyPayload,
      status: "degraded",
      database: { status: "down", latency_ms: null, detail: "Database is unreachable." },
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(degraded)));
    renderApp("/admin");

    expect(await screen.findByText("Unreachable")).toBeInTheDocument();
    expect(screen.getByText("Degraded")).toBeInTheDocument();
  });

  it("explains how to start the backend when the API is unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    renderApp("/admin");

    expect(await screen.findByText("Backend unavailable")).toBeInTheDocument();
    expect(screen.getByText(/can't reach the server/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText("API offline").length).toBeGreaterThan(0));
  });

  it.each([
    ["/job-analyzer", "Job analyzer"],
    ["/evaluation", "RAG evaluation"],
  ])("routes %s inside the dashboard", (path, heading) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(healthyPayload)));
    renderApp(path);
    expect(screen.getByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Dashboard" })).toBeInTheDocument();
  });
});
