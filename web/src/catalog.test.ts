import { describe, expect, it } from "vitest"

import {
  clampDistanceKm,
  dataRole,
  safeNextPath,
  tradeLabel,
  userDiscovery,
  zoneClass,
} from "./catalog"

describe("catálogo visual", () => {
  it("mapea roles de API a data-role", () => {
    expect(dataRole("CLIENTE")).toBe("cliente")
    expect(dataRole("PROVEEDOR")).toBe("proveedor")
    expect(dataRole("ADMINISTRADOR")).toBe("admin")
  })

  it("nunca trata un domicilio oculto como autorizado", () => {
    expect(zoneClass("OCULTO")).toContain("zone--oculto")
    expect(zoneClass("ZONA_APROXIMADA")).toContain("zone--aprox")
    expect(zoneClass("DOMICILIO_AUTORIZADO")).toContain("zone--autorizado")
  })

  it("nombra oficios en español", () => {
    expect(tradeLabel("herreria")).toBe("Herrería")
    expect(tradeLabel("plomeria")).toBe("Plomería")
  })

  it("lee la zona de descubrimiento de la cuenta", () => {
    expect(userDiscovery({ searchZone: "Coyoacán", maxDistanceKm: 8 })).toEqual({
      zone: "Coyoacán",
      maxDistanceKm: 8,
    })
    expect(userDiscovery({ search_zone: "Iztapalapa", max_distance_km: 1 }).maxDistanceKm).toBe(2)
    expect(clampDistanceKm(80)).toBe(50)
    expect(userDiscovery(null).zone).toBeNull()
  })

  it("solo acepta rutas internas después de entrar", () => {
    expect(safeNextPath("/calificados/1")).toBe("/calificados/1")
    expect(safeNextPath("https://evil.example")).toBe("/")
    expect(safeNextPath("//evil.example")).toBe("/")
  })
})
