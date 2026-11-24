import { Link } from "react-router-dom"

import type { ExploreProvider } from "../api/client"
import { useAuth } from "../auth/AuthContext"

export function ContactCta({
  provider,
  preferredTrade,
}: {
  provider: ExploreProvider
  preferredTrade?: string | null
}) {
  const { user } = useAuth()
  const ficha = preferredTrade
    ? `/calificados/${provider.id}?oficio=${encodeURIComponent(preferredTrade)}`
    : `/calificados/${provider.id}`
  const trade =
    preferredTrade && provider.trades.includes(preferredTrade)
      ? preferredTrade
      : provider.trades[0] ?? ""

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
  const query = new URLSearchParams({ proveedor: provider.id })
  if (trade) query.set("oficio", trade)
  return (
    <Link className="btn btn-primary" to={`/nuevo?${query}`}>
      Solicitar cotización
    </Link>
  )
}
