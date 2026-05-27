import type { AuthUser, CreateSearchJobPayload, RawListingsResponse, SearchJob, SuppliersResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function createSearchJob(payload: CreateSearchJobPayload): Promise<SearchJob> {
  const response = await fetch(`${API_BASE_URL}/api/search-jobs`, {
    method: "POST",
    credentials: "include",
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
  const response = await fetch(`${API_BASE_URL}/api/search-jobs/${jobId}/raw-listings`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Raw listing request failed with status ${response.status}`);
  }

  return response.json();
}

export async function getUniqueSuppliers(jobId: string): Promise<SuppliersResponse> {
  const response = await fetch(`${API_BASE_URL}/api/search-jobs/${jobId}/suppliers`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Supplier request failed with status ${response.status}`);
  }

  return response.json();
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error(`Login failed with status ${response.status}`);
  }

  return response.json();
}

export async function logout(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Logout failed with status ${response.status}`);
  }
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    credentials: "include",
  });

  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Session check failed with status ${response.status}`);
  }

  return response.json();
}
