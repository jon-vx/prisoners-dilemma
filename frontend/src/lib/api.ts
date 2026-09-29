import "server-only";

import type { Strategy } from "./types";

export interface Health {
  status: "ok" | "error";
  database: "connected" | "not_configured" | "unavailable";
}

// This URL is used by the Next.js server, never exposed to the browser.
const apiUrl = (
  process.env.API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const getStrategies = () => get<Strategy[]>("/strategies");
export const getHealth = () => get<Health>("/health");

// Keep browser requests on the same origin; FastAPI remains the source of validation.
export async function forwardApi(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      ...init,
      cache: "no-store",
      signal: AbortSignal.timeout(60_000),
    });
    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    console.error("Simulation API request failed", path, error);
    return Response.json(
      {
        detail: "The simulation service could not be reached. Please try again.",
      },
      { status: 503 },
    );
  }
}
