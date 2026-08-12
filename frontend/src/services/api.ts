const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiGet<T>(
  path: string,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      headers: {
        Accept: "application/json",
        ...(localStorage.getItem("cat_ci_token") ? { Authorization: `Bearer ${localStorage.getItem("cat_ci_token")}` } : {}),
      },
    },
  );

  if (!response.ok) {
    let message =
      `API request failed with ${response.status}`;

    try {
      const body = await response.json();

      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new ApiError(
      response.status,
      message,
    );
  }

  return response.json() as Promise<T>;
}

export async function apiRequest<T>(path: string, method = "POST", body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json", Accept: "application/json",
      ...(localStorage.getItem("cat_ci_token") ? { Authorization: `Bearer ${localStorage.getItem("cat_ci_token")}` } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(response.status, data.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}
