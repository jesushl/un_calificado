import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { AuthProvider } from "../auth/AuthContext"
import { ExplorePage } from "./ExplorePage"

const popularProviders = vi.fn()
const publicWorks = vi.fn()

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client")
  return {
    ...actual,
    api: {
      ...actual.api,
      popularProviders: (...args: unknown[]) => popularProviders(...args),
      publicWorks: (...args: unknown[]) => publicWorks(...args),
      me: vi.fn(),
    },
    getToken: () => null,
  }
})

describe("ExplorePage", () => {
  beforeEach(() => {
    popularProviders.mockResolvedValue({
      items: [
        {
          id: "prov-1",
          name: "Herrería La Palma",
          modality: "ORGANIZACION",
          trades: ["herreria"],
          coverage: ["Iztapalapa"],
          experienceYears: 16,
          generalAvailability: "Lunes a sábado",
          verified: true,
          rating: { average: 5, count: 4 },
          concludedCount: 2,
          coverImage: null,
        },
      ],
    })
    publicWorks.mockResolvedValue({
      items: [
        {
          id: "work-1",
          fileName: "reja.svg",
          contentType: "image/svg+xml",
          downloadUrl: "/api/v1/files/work-1/content",
          trade: "herreria",
          expectedOutcome: "Reja de patio que sí cierra",
          approximateZone: "Iztapalapa",
          provider: {
            id: "prov-1",
            name: "Herrería La Palma",
            trades: ["herreria"],
            coverage: ["Iztapalapa"],
            verified: true,
            rating: { average: 5, count: 4 },
            concludedCount: 2,
            modality: "ORGANIZACION",
            experienceYears: 16,
            generalAvailability: null,
            coverImage: null,
          },
        },
      ],
    })
  })

  it("muestra populares y fotos de obra sin sesión", async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <ExplorePage />
        </AuthProvider>
      </MemoryRouter>,
    )
    expect(await screen.findByRole("heading", { name: /Quien sí sabe/i })).toBeInTheDocument()
    expect(await screen.findByText("Herrería La Palma")).toBeInTheDocument()
    expect(screen.getByAltText(/Reja de patio que sí cierra/i)).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Entra para contactar" })).toHaveAttribute(
      "href",
      "/entrar?siguiente=%2Fcalificados%2Fprov-1",
    )
    expect(screen.queryByText(/calle/i)).not.toBeInTheDocument()
  })
})
