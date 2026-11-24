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
  searchZone?: string | null
  search_zone?: string | null
  maxDistanceKm?: number
  max_distance_km?: number
}

export type DiscoveryZone = { id: string; label: string }

export type Discovery = {
  applied: boolean
  searchZone?: string | null
  maxDistanceKm?: number
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
  distanceKm?: number
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

export type Appointment = {
  id: string
  requestId: string
  startsAt: string
  endsAt: string
  costMxn: number
  confirmedByClient: boolean
  confirmedByProvider: boolean
  isVisit: boolean
  status: string
  expiresAt: string | null
}

export type ProposalMaterial = {
  description: string
  quantity: number
  unit: string
  unitPriceMxn: number
  subtotalMxn: number
  brandOrQuality?: string
}

export type Proposal = {
  id: string
  requestId: string
  workDescription: string
  dates: string[]
  laborSubtotalMxn: number
  materials: ProposalMaterial[]
  additionalCostsMxn: number
  totalMxn: number
  version: number
  status: string
  issuedAt: string
  expiresAt: string
}

export type ProjectMessage = {
  id: string
  content: string
  senderId: string
  sentAt: string
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
  updateMe(payload: {
    name?: string
    phone?: string
    searchZone?: string
    maxDistanceKm?: number
  }) {
    return request<User>("/api/v1/users/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  },
  discoveryZones() {
    return request<{ items: DiscoveryZone[] }>("/api/v1/explore/zones")
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
  popularProviders(oficio?: string, zona?: string, radioKm?: number, q?: string) {
    const params = new URLSearchParams()
    if (oficio) params.set("oficio", oficio)
    if (zona) params.set("zona", zona)
    if (radioKm) params.set("radioKm", String(radioKm))
    if (q) params.set("q", q)
    const query = params.toString() ? `?${params}` : ""
    return request<{
      items: ExploreProvider[]
      discovery?: Discovery
      query?: string | null
      noResultsMessage?: string | null
    }>(`/api/v1/explore/providers${query}`)
  },
  publicProvider(id: string) {
    return request<ExploreProvider>(`/api/v1/explore/providers/${id}`)
  },
  publicWorks(oficio?: string, zona?: string, radioKm?: number, q?: string) {
    const params = new URLSearchParams()
    if (oficio) params.set("oficio", oficio)
    if (zona) params.set("zona", zona)
    if (radioKm) params.set("radioKm", String(radioKm))
    if (q) params.set("q", q)
    const query = params.toString() ? `?${params}` : ""
    return request<{ items: ExploreWork[]; discovery?: Discovery; query?: string | null }>(
      `/api/v1/explore/works${query}`,
    )
  },
  contactProvider(
    providerId: string,
    payload: {
      expectedOutcome: string
      approximateZone: string
      trade?: string
      desiredDate?: string
      description?: string
    },
  ) {
    return request<ServiceRequest>(`/api/v1/explore/providers/${providerId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  providerDecision(requestId: string, decision: "ACEPTAR" | "RECHAZAR") {
    return request<ServiceRequest>(`/api/v1/requests/${requestId}/provider-decision`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    })
  },
  listAppointments(requestId?: string) {
    const query = requestId ? `?requestId=${encodeURIComponent(requestId)}` : ""
    return request<{ items: Appointment[] }>(`/api/v1/appointments${query}`)
  },
  createAppointment(payload: {
    requestId: string
    startsAt: string
    endsAt: string
    costMxn: number
    confirmedByProvider: boolean
    isVisit?: boolean
  }) {
    return request<Appointment>("/api/v1/appointments", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  updateAppointment(
    appointmentId: string,
    payload: {
      confirmedByClient?: boolean
      confirmedByProvider?: boolean
      startsAt?: string
      endsAt?: string
    },
  ) {
    return request<Appointment>(`/api/v1/appointments/${appointmentId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  },
  cancelAppointment(appointmentId: string, reason: string) {
    return request<Appointment>(`/api/v1/appointments/${appointmentId}`, {
      method: "DELETE",
      body: JSON.stringify({ reason }),
    })
  },
  listProposals(requestId: string) {
    return request<{ items: Proposal[] }>(
      `/api/v1/proposals?requestId=${encodeURIComponent(requestId)}`,
    )
  },
  createProposal(payload: {
    requestId: string
    workDescription: string
    dates?: string[]
    laborSubtotalMxn: number
    materials: ProposalMaterial[]
    additionalCostsMxn: number
    totalMxn: number
  }) {
    return request<Proposal>("/api/v1/proposals", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  decideProposal(proposalId: string, decision: "ACEPTAR" | "RECHAZAR" | "PEDIR_CAMBIOS") {
    return request<Proposal>(`/api/v1/proposals/${proposalId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    })
  },
  listMessages(requestId: string) {
    return request<{ items: ProjectMessage[] }>(`/api/v1/requests/${requestId}/messages`)
  },
  sendMessage(requestId: string, content: string) {
    return request<ProjectMessage>(`/api/v1/requests/${requestId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    })
  },
  updateRequestStatus(requestId: string, status: string, reason?: string) {
    return request<ServiceRequest>(`/api/v1/requests/${requestId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, reason }),
    })
  },
  createEvaluation(
    requestId: string,
    payload: {
      subjectType: "PROVEEDOR" | "CLIENTE"
      score: number
      punctuality?: number
      quality?: number
      cleanliness?: number
      budgetAdherence?: number
      comment?: string
    },
  ) {
    return request<{
      id: string
      subjectType: string
      score: number
      status: string
      createdAt: string
    }>(`/api/v1/requests/${requestId}/evaluations`, {
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
