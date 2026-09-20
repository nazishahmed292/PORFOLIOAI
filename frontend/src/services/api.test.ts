import { describe, expect, it, vi } from "vitest";

import { jsonResponse } from "@/test/utils";

import { api, ApiError } from "./api";
import { authToken } from "./authToken";

describe("api client", () => {
  it("returns parsed JSON on success", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ hello: "world" })));
    await expect(api.get("/anything")).resolves.toEqual({ hello: "world" });
  });

  it("turns the backend error format into an ApiError", async () => {
    const body = { error: { code: "not_found", message: "Project not found", details: null } };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body, 404)));

    const error = await api.get("/projects/9").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: "not_found", message: "Project not found" });
  });

  it("reports an unreachable server as a friendly network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const error = (await api.get("/health").catch((e: unknown) => e)) as ApiError;
    expect(error.isNetworkError).toBe(true);
    expect(error.message).toMatch(/can't reach the server/i);
  });

  it("falls back to a generic message when the error body is not JSON", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>Bad gateway</html>", { status: 502 })));

    const error = (await api.get("/health").catch((e: unknown) => e)) as ApiError;
    expect(error.status).toBe(502);
    expect(error.message).toBe("Request failed (502).");
  });

  it("sends the JWT when one is stored, and JSON bodies with the right header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    authToken.set("token-123");

    await api.post("/skills", { name: "Python" });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(url).toBe("/api/skills");
    expect(headers.get("Authorization")).toBe("Bearer token-123");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(init.body).toBe(JSON.stringify({ name: "Python" }));
  });
});
