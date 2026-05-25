import type { CreateSearchJobPayload, RawListingsResponse, SearchJob } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function createSearchJob(payload: CreateSearchJobPayload): Promise<SearchJob> {
  const response = await fetch(`${API_BASE_URL}/api/search-jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Search request failed with status ${response.status}`);
  }

  return response.json();
}

export async function getRawListings(jobId: string): Promise<RawListingsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/search-jobs/${jobId}/raw-listings`);

  if (!response.ok) {
    throw new Error(`Raw listing request failed with status ${response.status}`);
  }

  return response.json();
}
