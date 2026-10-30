import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { AuthProvider } from "../auth/AuthContext"
import { SettingsPage } from "./SettingsPage"

const discoveryZones = vi.fn()
const updateMe = vi.fn()
const me = vi.fn()

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client")
  return {
    ...actual,
    api: {
      ...actual.api,
      discoveryZones: (...args: unknown[]) => discoveryZones(...args),
      updateMe: (...args: unknown[]) => updateMe(...args),
      me: (...args: unknown[]) => me(...args),
    },
    getToken: () => "token",
  }
})

describe("SettingsPage", () => {
  beforeEach(() => {
    sessionStorage.clear()
    discoveryZones.mockResolvedValue({
      items: [
        { id: "Coyoacán", label: "Coyoacán" },
        { id: "Iztapalapa", label: "Iztapalapa" },
      ],
    })
    me.mockResolvedValue({
      id: "user-1",
      email: "ana@example.com",
      role: "CLIENTE",
      searchZone: null,
      maxDistanceKm: 15,
    })
    updateMe.mockResolvedValue({
      id: "user-1",
      email: "ana@example.com",
      role: "CLIENTE",
      searchZone: "Coyoacán",
      maxDistanceKm: 8,
    })
  })

  it("guarda alcaldía y distancia de la cuenta", async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={["/cuenta"]}>
        <AuthProvider>
          <Routes>
            <Route path="/cuenta" element={<SettingsPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(await screen.findByRole("heading", { name: /A quién ves cerca/i })).toBeInTheDocument()
    await user.click(await screen.findByRole("button", { name: "Coyoacán" }))
    await user.click(screen.getByRole("button", { name: "Guardar zona" }))
    expect(updateMe).toHaveBeenCalledWith({ searchZone: "Coyoacán", maxDistanceKm: 15 })
    expect(await screen.findByRole("status")).toHaveTextContent("Cambios guardados.")
    expect(document.body.textContent).not.toMatch(/Calle\s+\d+/)
  })
})
