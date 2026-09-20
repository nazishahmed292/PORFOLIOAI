/**
 * Where the JWT lives in the browser. Authentication itself arrives in Phase 3;
 * the API client already reads the token from here so nothing else needs to change.
 */
const TOKEN_KEY = "portfolioai-token";

export const authToken = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string): void {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      /* storage unavailable (private mode): the user simply has to sign in again */
    }
  },
  clear(): void {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  },
};
