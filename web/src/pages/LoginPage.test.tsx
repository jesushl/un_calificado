import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi } from "vitest"

import { AuthProvider } from "../auth/AuthContext"
import { LoginPage } from "./LoginPage"

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client")
  return {
    ...actual,
    api: {
      ...actual.api,
      login: vi.fn(),
      me: vi.fn(),
    },
    getToken: () => null,
  }
})

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe("LoginPage", () => {
  it("pide el correo si se envía vacío", async () => {
    const user = userEvent.setup()
    renderLogin()
    await user.click(screen.getByRole("button", { name: "Entrar" }))
    expect(screen.getByRole("alert")).toHaveTextContent("Escribe tu correo electrónico.")
  })

  it("muestra el titular de taller", () => {
    renderLogin()
    expect(screen.getByRole("heading", { name: /Entra y sigue con tu proyecto/i })).toBeInTheDocument()
    expect(screen.getByText(/domicilio exacto/i)).toBeInTheDocument()
  })

  it("ofrece Google, Facebook y TikTok", () => {
    renderLogin()
    expect(screen.getByRole("button", { name: "Continuar con Google" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Continuar con Facebook" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Continuar con TikTok" })).toBeInTheDocument()
  })
})
