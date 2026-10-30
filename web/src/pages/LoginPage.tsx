import { useState, type FormEvent } from "react"
import { Link, Navigate, useSearchParams } from "react-router-dom"

import { Wordmark } from "../brand/Mark"
import { useAuth } from "../auth/AuthContext"
import { OAuthButtons } from "../components/OAuthButtons"
import { safeNextPath } from "../catalog"

export function LoginPage() {
  const { user, login, error } = useAuth()
  const [params] = useSearchParams()
  const next = safeNextPath(params.get("siguiente"))
  const oauthError = params.get("oauth_error")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [fieldError, setFieldError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const expired = params.get("expired")

  if (user) return <Navigate to={next} replace />

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!email.trim()) {
      setFieldError("Escribe tu correo electrónico.")
      return
    }
    if (!password) {
      setFieldError("Escribe tu contraseña.")
      return
    }
    setFieldError(null)
    setPending(true)
    try {
      await login(email.trim(), password)
    } catch {
      /* el mensaje vive en AuthContext */
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="plano" style={{ minHeight: "100dvh", display: "grid", placeItems: "center", padding: "var(--space-6)" }}>
      <section className="stack" style={{ width: "min(28rem, 100%)" }}>
        <Wordmark to="/" />
        <p className="eyebrow">Entrar</p>
        <h1>Entra y sigue con tu proyecto.</h1>
        <p>Tu domicilio exacto solo lo ve quien tú autorices.</p>
        {expired ? <p className="alert" role="status">Tu sesión venció. Entra de nuevo para seguir donde ibas.</p> : null}
        {oauthError ? (
          <p className="alert alert--warn" role="alert">
            {oauthError}
          </p>
        ) : null}
        {error ? (
          <p className="alert alert--danger" role="alert">
            {error}
          </p>
        ) : null}
        {fieldError ? (
          <p className="alert alert--danger" role="alert">
            {fieldError}
          </p>
        ) : null}
        <form className="stack" onSubmit={(event) => void onSubmit(event)} noValidate>
          <label className="field">
            <span className="field-label">Correo electrónico</span>
            <input
              className="input"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="nombre@correo.mx"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="field">
            <span className="field-label">Contraseña</span>
            <input
              className="input"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setShowPassword((value) => !value)}
            >
              {showPassword ? "Ocultar" : "Mostrar"}
            </button>
          </label>
          <button className="btn btn-primary btn-block" type="submit" disabled={pending}>
            {pending ? "Entrando…" : "Entrar"}
          </button>
        </form>
        <p className="oauth-or">o con tu cuenta de siempre</p>
        <OAuthButtons next={next === "/" ? undefined : next} />
        <p>
          ¿Primera vez en UnCalificado?{" "}
          <Link to={next === "/" ? "/registro" : `/registro?siguiente=${encodeURIComponent(next)}`}>
            Crea tu cuenta
          </Link>
        </p>
      </section>
    </main>
  )
}
