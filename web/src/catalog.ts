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

export function safeNextPath(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("://")) {
    return "/"
  }
  return value
}
