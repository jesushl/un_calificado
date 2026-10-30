import { useEffect, useState } from "react"
import { Link, Navigate, useSearchParams } from "react-router-dom"

import { api, ApiError } from "../api/client"
import { useAuth } from "../auth/AuthContext"
import { Wordmark } from "../brand/Mark"
import { safeNextPath } from "../catalog"

export function OAuthCallbackPage() {
  const { user, acceptSession } = useAuth()
  const [params] = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const next = safeNextPath(params.get("siguiente"))

  useEffect(() => {
    const code = params.get("code")
    if (!code) {
      setError("Faltó el código de acceso. Entra de nuevo.")
      return
    }
    api
      .exchangeOAuth(code)
      .then((response) => acceptSession(response.access_token, response.user))
      .catch((caught: unknown) => {
        setError(
          caught instanceof ApiError
            ? caught.message
            : "No pudimos conectar. Revisa tu internet y vuelve a intentar.",
        )
      })
  }, [acceptSession, params])

  if (user) return <Navigate to={next} replace />

  return (
    <main className="plano" style={{ minHeight: "100dvh", display: "grid", placeItems: "center", padding: "var(--space-6)" }}>
      <section className="stack" style={{ width: "min(28rem, 100%)" }}>
        <Wordmark to="/" />
        <h1>Entrando con tu cuenta</h1>
        {error ? (
          <p className="alert alert--danger" role="alert">
            {error} <Link to="/entrar">Volver a entrar</Link>
          </p>
        ) : (
          <p>Un momento, estamos abriendo tu sesión.</p>
        )}
      </section>
    </main>
  )
}
