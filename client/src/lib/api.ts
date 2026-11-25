// Thin fetch wrapper for the Flask backend under /api.
// Pattern follows contexts/SystemSettingsContext.tsx (credentials: 'include',
// unwrap { data } envelope) — see that file for the original reference.

export class ApiError extends Error {
  status: number
  // The error envelope's optional "data" (e.g. which devices were rejected).
  data: unknown

  constructor(message: string, status: number, data?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

// Sent when a request is refused because there is no signed-in session, for
// example after an administrator changed the account. SessionTimeoutWatcher
// listens and goes to the login page.
export const UNAUTHORIZED_EVENT = 'pinpoint-unauthorized'

export function reportUnauthorized() {
  window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) }
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(path, {
    credentials: 'include',
    ...options,
    headers,
  })

  // 401s from @login_required hit Flask's default HTML error page, not our
  // JSON envelope — guard the parse instead of assuming res.json() works.
  const text = await res.text()
  let body: { success?: boolean; message?: string; data?: unknown } | null = null
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = null
    }
  }

  if (!res.ok) {
    if (res.status === 401) {
      reportUnauthorized()
    }
    const fallback =
      res.status === 401
        ? 'You must be signed in to do that.'
        : `Request failed (${res.status})`
    throw new ApiError(body?.message ?? fallback, res.status, body?.data)
  }

  return (body && 'data' in body ? body.data : body) as T
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path)
}

export function apiPost<T>(path: string, data?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: data !== undefined ? JSON.stringify(data) : undefined,
  })
}

export function apiPut<T>(path: string, data?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    body: data !== undefined ? JSON.stringify(data) : undefined,
  })
}

export function apiDelete<T>(path: string, data?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'DELETE',
    body: data !== undefined ? JSON.stringify(data) : undefined,
  })
}

export function errorMessage(err: unknown, fallback = 'Something went wrong.'): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return fallback
}
