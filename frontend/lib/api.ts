const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface URLSubmitResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface URLResult {
  url: string;
  title: string | null;
  description: string | null;
  status_code: number | null;
  response_time_ms: number | null;
  redirect_chain: string[];
  ssl_valid: boolean | null;
  ssl_expires_at: string | null;
  tech_stack: string[];
  safety_score: "safe" | "suspicious" | "dangerous" | null;
  screenshot_url: string | null;
  analyzed_at: string | null;
}

export interface URLResponse {
  id: string;
  url: string;
  url_hash: string;
  status: string;
  created_at: string;
  result: URLResult | null;
}

export interface PaginatedURLResponse {
  items: URLResponse[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export async function submitUrl(url: string): Promise<URLSubmitResponse | URLResponse> {
  const res = await fetch(`${API_URL}/api/v1/urls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (res.status === 429) {
    throw new Error("Rate limit exceeded. Please try again later.");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit URL");
  }

  return res.json();
}

export async function getUrlResult(id: string): Promise<URLResponse> {
  const res = await fetch(`${API_URL}/api/v1/urls/${id}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch result");
  }

  return res.json();
}

export async function listUrls(
  page: number = 1,
  limit: number = 20
): Promise<PaginatedURLResponse> {
  const res = await fetch(
    `${API_URL}/api/v1/urls?page=${page}&limit=${limit}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error("Failed to fetch URLs");
  }

  return res.json();
}

export async function simulateTraffic(): Promise<void> {
  const res = await fetch(`${API_URL}/api/v1/simulate`, {
    method: "POST",
  });

  if (!res.ok) {
    throw new Error("Failed to simulate traffic");
  }
}
