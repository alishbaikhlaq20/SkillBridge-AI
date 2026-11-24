/**
 * Shared helpers for talking to the FastAPI backend.
 *
 * - The backend URL comes from NEXT_PUBLIC_API_URL (set it in
 *   frontend/.env.local), with the local development address as a fallback.
 * - apiFetch adds the login token, turns every failure into an ApiError with a
 *   readable message, and sends the user to /login when the token is missing
 *   or expired.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "access_token";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function redirectToLogin() {
  if (typeof window !== "undefined") {
    // A full page load on purpose: this runs outside React (no router is
    // available here) and it also clears any state left from the old session.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/login";
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window === "undefined"
      ? null
      : localStorage.getItem(TOKEN_KEY);

  if (!token) {
    redirectToLogin();
    throw new ApiError("Please log in to continue.", 401);
  }

  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new ApiError(
      "Could not reach the server. Please check that the backend is running.",
      0
    );
  }

  let data: unknown = null;

  try {
    data = await response.json();
  } catch {
    // The response had no JSON body.
  }

  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    redirectToLogin();
    throw new ApiError(
      "Your session has expired. Please log in again.",
      401
    );
  }

  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;

    throw new ApiError(
      typeof detail === "string"
        ? detail
        : "The request could not be completed.",
      response.status
    );
  }

  return data as T;
}
