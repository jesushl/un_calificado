import { useState } from "react"

import { api, ApiError } from "../api/client"

const NETWORKS = [
  { id: "google" as const, label: "Continuar con Google" },
  { id: "facebook" as const, label: "Continuar con Facebook" },
  { id: "tiktok" as const, label: "Continuar con TikTok" },
]

export function OAuthButtons({
  role = "CLIENTE",
  next,
}: {
  role?: "CLIENTE" | "PROVEEDOR"
  next?: string
}) {
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<string | null>(null)

  async function start(provider: string) {
    setError(null)
    setPending(provider)
    try {
      const started = await api.startOAuth(provider, role, next)
      window.location.assign(started.authorizationUrl)
    } catch (caught) {
      setPending(null)
      if (caught instanceof ApiError && caught.status === 503) {
        setError(caught.message)
        return
      }
      setError(
        caught instanceof ApiError
          ? caught.message
          : "No pudimos conectar. Revisa tu internet y vuelve a intentar.",
      )
    }
  }

  return (
    <div className="oauth">
      <p className="oauth-note">
        Al continuar con Google, Facebook o TikTok aceptas el aviso de privacidad y declaras ser
        mayor de edad.
      </p>
      {error ? (
        <p className="alert alert--warn" role="alert">
          {error}
        </p>
      ) : null}
      <div className="oauth-list">
        {NETWORKS.map((network) => (
          <button
            key={network.id}
            type="button"
            className="btn btn-oauth"
            data-network={network.id}
            disabled={pending !== null}
            onClick={() => void start(network.id)}
          >
            {pending === network.id ? "Redirigiendo…" : network.label}
          </button>
        ))}
      </div>
    </div>
  )
}
