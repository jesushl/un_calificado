import { Link } from "react-router-dom"

import type { ExploreProvider } from "../api/client"
import { useAuth } from "../auth/AuthContext"

export function ContactCta({ provider }: { provider: ExploreProvider }) {
  const { user } = useAuth()
  const ficha = `/calificados/${provider.id}`

  if (!user) {
    return (
      <Link className="btn btn-primary" to={`/entrar?siguiente=${encodeURIComponent(ficha)}`}>
        Entra para contactar
      </Link>
    )
  }
  if (user.role !== "CLIENTE") {
    return <p className="ficha-meta">El contacto lo inicia un cliente con cuenta.</p>
  }
  return (
    <Link
      className="btn btn-primary"
      to={`/nuevo?proveedor=${provider.id}&oficio=${provider.trades[0] ?? ""}`}
    >
      Solicitar cotización
    </Link>
  )
}
