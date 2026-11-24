export const TRADES = [
  { id: "albanileria", key: "ALB", label: "Albañilería" },
  { id: "plomeria", key: "PLO", label: "Plomería" },
  { id: "electricidad", key: "ELE", label: "Electricidad" },
  { id: "carpinteria", key: "CAR", label: "Carpintería" },
  { id: "herreria", key: "HER", label: "Herrería" },
  { id: "pintura", key: "PIN", label: "Pintura" },
  { id: "pisos_azulejos", key: "PIS", label: "Pisos y azulejos" },
  { id: "vidrieria_canceleria", key: "VID", label: "Vidriería" },
  { id: "tablaroca", key: "TAB", label: "Tablaroca" },
  { id: "impermeabilizacion", key: "IMP", label: "Impermeabilización" },
] as const

export const PROJECT_STATUS: Record<string, string> = {
  BORRADOR: "Borrador",
  CONFIRMADA: "Confirmada",
  PROGRAMADO: "Programado",
  EN_PROCESO: "En proceso",
  TERMINADO: "Terminado",
  CONCLUIDO: "Concluido",
}

export const APPOINTMENT_STATUS: Record<string, string> = {
  PENDIENTE: "Pendiente de confirmar",
  CONFIRMADA: "Confirmada",
  EXPIRADA: "Expirada",
  CANCELADA: "Cancelada",
}

export const PROPOSAL_STATUS: Record<string, string> = {
  ENVIADA: "Enviada",
  ACEPTADA: "Aceptada",
  NEGOCIACION: "En negociación",
  RECHAZADA: "Rechazada",
  EXPIRADA: "Expirada",
}

export function formatMxn(value: number): string {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Mexico_City",
  }).format(date)
}

/** Fecha de hoy en Ciudad de México (YYYY-MM-DD) para inputs type=date. */
export function todayIsoMexico(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Mexico_City",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date())
}

export function isPastDate(isoDate: string, today = todayIsoMexico()): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(isoDate)) return true
  return isoDate < today
}

export const RULER_FILL: Record<string, number> = {
  BORRADOR: 0,
  CONFIRMADA: 20,
  PROGRAMADO: 40,
  EN_PROCESO: 60,
  TERMINADO: 80,
  CONCLUIDO: 100,
}

export type ApiRole = "CLIENTE" | "PROVEEDOR" | "ADMINISTRADOR"

export function dataRole(role: ApiRole | string | undefined): "cliente" | "proveedor" | "admin" {
  if (role === "PROVEEDOR") return "proveedor"
  if (role === "ADMINISTRADOR") return "admin"
  return "cliente"
}

export function zoneClass(visibility: string | undefined): string {
  if (visibility === "DOMICILIO_AUTORIZADO") return "zone zone--autorizado"
  if (visibility === "OCULTO") return "zone zone--oculto"
  return "zone zone--aprox"
}

export function tradeLabel(id: string | null | undefined): string {
  return TRADES.find((item) => item.id === id)?.label ?? id ?? "Oficio"
}

export function tradeKey(id: string | null | undefined): string {
  return TRADES.find((item) => item.id === id)?.key ?? "OFC"
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).slice(0, 2)
  return parts.map((part) => part[0]?.toUpperCase() ?? "").join("") || "UC"
}

export function accountLabel(user: {
  name?: string | null
  email?: string | null
  role?: string
} | null): string {
  if (!user) return ""
  const named = user.name?.trim()
  if (named) return named
  const email = user.email?.trim()
  if (email) return email.split("@")[0] || email
  if (user.role === "PROVEEDOR") return "Proveedor"
  if (user.role === "ADMINISTRADOR") return "Administrador"
  return "Cliente"
}

export const MIN_DISTANCE_KM = 2
export const MAX_DISTANCE_KM = 50
export const DEFAULT_DISTANCE_KM = 15
const DISCOVERY_KEY = "uncalificado.discovery"

export function clampDistanceKm(value: number | null | undefined): number {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return DEFAULT_DISTANCE_KM
  return Math.min(MAX_DISTANCE_KM, Math.max(MIN_DISTANCE_KM, Math.round(parsed)))
}

export function userDiscovery(user: {
  searchZone?: string | null
  search_zone?: string | null
  maxDistanceKm?: number
  max_distance_km?: number
} | null) {
  return {
    zone: user?.searchZone || user?.search_zone || null,
    maxDistanceKm: clampDistanceKm(user?.maxDistanceKm ?? user?.max_distance_km),
  }
}

export function readGuestDiscovery(): { zone: string | null; maxDistanceKm: number } {
  try {
    const raw = sessionStorage.getItem(DISCOVERY_KEY)
    if (!raw) return { zone: null, maxDistanceKm: DEFAULT_DISTANCE_KM }
    const parsed = JSON.parse(raw) as { zone?: unknown; maxDistanceKm?: unknown }
    return {
      zone: typeof parsed.zone === "string" && parsed.zone.trim() ? parsed.zone : null,
      maxDistanceKm: clampDistanceKm(parsed.maxDistanceKm as number),
    }
  } catch {
    return { zone: null, maxDistanceKm: DEFAULT_DISTANCE_KM }
  }
}

export function writeGuestDiscovery(zone: string | null, maxDistanceKm: number) {
  sessionStorage.setItem(
    DISCOVERY_KEY,
    JSON.stringify({ zone, maxDistanceKm: clampDistanceKm(maxDistanceKm) }),
  )
}

export function safeNextPath(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("://")) {
    return "/"
  }
  return value
}
