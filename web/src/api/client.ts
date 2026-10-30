const TOKEN_KEY = "uncalificado.token"

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, message: string, body: unknown) {
    super(message)
    this.status = status
    this.body = body
  }
}

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null): void {
  if (token) sessionStorage.setItem(TOKEN_KEY, token)
  else sessionStorage.removeItem(TOKEN_KEY)
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set("Content-Type", "application/json")
  const token = getToken()
  if (token) headers.set("Authorization", `Bearer ${token}`)
  let response: Response
  try {
    response = await fetch(path, { ...init, headers })
  } catch {
    throw new ApiError(0, "No pudimos conectar. Revisa tu internet y vuelve a intentar.", null)
  }
  if (response.status === 204) return undefined as T
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const message =
      body?.message ||
      body?.detail ||
      (response.status === 401
        ? "Tu sesión venció. Entra de nuevo para seguir."
        : "Algo falló de nuestro lado. Intenta de nuevo en unos minutos.")
    throw new ApiError(response.status, message, body)
  }
  return body as T
}

export type User = {
  id: string
  email: string
  role: "CLIENTE" | "PROVEEDOR" | "ADMINISTRADOR"
  status?: string
  name?: string | null
  phone?: string | null
  privacy_consent_version?: string
  created_at?: string
}

export type AuthResponse = {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export type ServiceRequest = {
  id: string
  expectedOutcome: string
  trade: string
  approximateZone: string
  desiredDate: string | null
  description: string | null
  status: string
  selectedProviderId: string | null
  createdAt: string
  updatedAt: string
}

export type ExploreProvider = {
  id: string
  name: string
  modality: "TRABAJADOR" | "ORGANIZACION"
  trades: string[]
  coverage: string[]
  experienceYears: number
  generalAvailability: string | null
  verified: boolean
  rating: { average: number; count: number }
  concludedCount: number
  coverImage: { id: string; downloadUrl: string; fileName: string } | null
}

export type ExploreWork = {
  id: string
  fileName: string
  contentType: string
  downloadUrl: string
  trade: string
  expectedOutcome: string
  approximateZone: string
  provider: ExploreProvider
}

export type OAuthNetwork = {
  id: "google" | "facebook" | "tiktok"
  label: string
  configured: boolean
}

export const api = {
  register(payload: {
    email: string
    password: string
    role: "CLIENTE" | "PROVEEDOR"
    privacy_consent_version: string
    adult_declaration: boolean
  }) {
    return request<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  login(email: string, password: string) {
    return request<AuthResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
  },
  logout() {
    return request<void>("/api/v1/auth/logout", { method: "POST" })
  },
  me() {
    return request<User>("/api/v1/users/me")
  },
  listRequests(estado?: string) {
    const query = estado ? `?estado=${encodeURIComponent(estado)}` : ""
    return request<{ items: ServiceRequest[] }>(`/api/v1/requests${query}`)
  },
  createRequest(payload: {
    expectedOutcome: string
    trade: string
    approximateZone: string
    desiredDate?: string
    description?: string
    manualCapture?: boolean
  }) {
    return request<ServiceRequest>("/api/v1/requests", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  getRequest(id: string) {
    return request<ServiceRequest>(`/api/v1/requests/${id}`)
  },
  confirmRequest(id: string) {
    return request<ServiceRequest>(`/api/v1/requests/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ summaryConfirmed: true }),
    })
  },
  getPrivacy(id: string) {
    return request<{
      visibility: string
      municipality?: string
      neighborhood?: string
      exactAddress?: string | null
    }>(`/api/v1/requests/${id}/privacy`)
  },
  listProviders(oficio?: string, zona?: string) {
    const params = new URLSearchParams()
    if (oficio) params.set("oficio", oficio)
    if (zona) params.set("zona", zona)
    const query = params.toString() ? `?${params}` : ""
    return request<{ items: Array<Record<string, unknown>>; noResultsMessage?: string | null }>(
      `/api/v1/providers${query}`,
    )
  },
  availabilityReport(month: string) {
    return request<{
      month: string
      availabilityPercent: number
    }>(`/api/v1/admin/availability-reports?month=${month}`)
  },
  popularProviders(oficio?: string) {
    const query = oficio ? `?oficio=${encodeURIComponent(oficio)}` : ""
    return request<{ items: ExploreProvider[] }>(`/api/v1/explore/providers${query}`)
  },
  publicProvider(id: string) {
    return request<ExploreProvider>(`/api/v1/explore/providers/${id}`)
  },
  publicWorks(oficio?: string) {
    const query = oficio ? `?oficio=${encodeURIComponent(oficio)}` : ""
    return request<{ items: ExploreWork[] }>(`/api/v1/explore/works${query}`)
  },
  contactProvider(
    providerId: string,
    payload: { expectedOutcome: string; approximateZone: string; trade?: string },
  ) {
    return request<ServiceRequest>(`/api/v1/explore/providers/${providerId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  oauthProviders() {
    return request<{ items: OAuthNetwork[] }>("/api/v1/auth/oauth/providers")
  },
  startOAuth(provider: string, role: "CLIENTE" | "PROVEEDOR", next?: string) {
    const params = new URLSearchParams({ role })
    if (next) params.set("next", next)
    return request<{ authorizationUrl: string; provider: string }>(
      `/api/v1/auth/oauth/${provider}?${params}`,
    )
  },
  exchangeOAuth(code: string) {
    return request<AuthResponse>("/api/v1/auth/oauth/exchange", {
      method: "POST",
      body: JSON.stringify({ code }),
    })
  },
}
