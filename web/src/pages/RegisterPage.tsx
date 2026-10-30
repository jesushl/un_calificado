import { useState, type FormEvent } from "react"
import { Link, Navigate, useSearchParams } from "react-router-dom"

import { ApiError } from "../api/client"
import { Wordmark } from "../brand/Mark"
import { useAuth } from "../auth/AuthContext"
import { OAuthButtons } from "../components/OAuthButtons"
import { safeNextPath } from "../catalog"

export function RegisterPage() {
  const { user, register } = useAuth()
  const [params] = useSearchParams()
  const next = safeNextPath(params.get("siguiente"))
  const [role, setRole] = useState<"CLIENTE" | "PROVEEDOR">("CLIENTE")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  if (user) return <Navigate to={next} replace />

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!consent) {
      setError("Marca que leíste el aviso de privacidad para crear tu cuenta.")
      return
    }
    if (password.length < 10) {
      setError(`Tu contraseña necesita al menos 10 caracteres. Te faltan ${10 - password.length}.`)
      return
    }
    setError(null)
    setPending(true)
    try {
      await register({ email: email.trim(), password, role })
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 409) {
        setError("Ese correo ya tiene una cuenta. Entra o cambia tu contraseña.")
      } else if (caught instanceof ApiError) {
        setError(caught.message)
      } else {
        setError("No pudimos conectar. Revisa tu internet y vuelve a intentar.")
      }
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="plano" style={{ minHeight: "100dvh", padding: "var(--space-7) var(--space-5)" }}>
      <div className="container container--narrow stack">
        <Wordmark to="/entrar" />
        <p className="eyebrow">Crea tu cuenta</p>
        <h1>¿Qué vienes a hacer?</h1>
        {error ? (
          <p className="alert alert--danger" role="alert">
            {error}
          </p>
        ) : null}
        <form className="stack" onSubmit={(event) => void onSubmit(event)}>
          <fieldset className="choice-group choice-group--2">
            <legend className="sr-only">Rol</legend>
            <label className="choice choice--cliente">
              <input
                type="radio"
                name="role"
                value="CLIENTE"
                checked={role === "CLIENTE"}
                onChange={() => setRole("CLIENTE")}
              />
              <span className="choice-body">
                <span className="choice-title">Necesito un oficio</span>
                <span className="choice-desc">Cuento qué hace falta y elijo a quién contratar.</span>
              </span>
            </label>
            <label className="choice choice--proveedor">
              <input
                type="radio"
                name="role"
                value="PROVEEDOR"
                checked={role === "PROVEEDOR"}
                onChange={() => setRole("PROVEEDOR")}
              />
              <span className="choice-body">
                <span className="choice-title">Ofrezco un oficio</span>
                <span className="choice-desc">Como trabajador independiente o con mi organización.</span>
              </span>
            </label>
          </fieldset>
          <label className="field">
            <span className="field-label">Correo electrónico</span>
            <input
              className="input"
              name="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <span className="field-hint">Aquí te avisamos de citas y propuestas.</span>
          </label>
          <label className="field">
            <span className="field-label">Contraseña</span>
            <input
              className="input"
              name="password"
              type="password"
              required
              minLength={10}
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <span className="field-hint">Mínimo 10 caracteres. Una frase larga funciona mejor que un símbolo raro.</span>
          </label>
          <label className="check">
            <input
              type="checkbox"
              name="consent"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            <span>Leí el aviso de privacidad. Tu domicilio exacto nunca se publica.</span>
          </label>
          <p>UnCalificado no cobra ni procesa pagos. El pago lo acuerdas directamente con el proveedor.</p>
          <button className="btn btn-primary" type="submit" disabled={pending}>
            {pending ? "Creando tu cuenta…" : "Crear cuenta"}
          </button>
        </form>
        <p className="oauth-or">o con tu cuenta de siempre</p>
        <OAuthButtons role={role} next={next === "/" ? undefined : next} />
        <p>
          ¿Ya tienes cuenta?{" "}
          <Link to={next === "/" ? "/entrar" : `/entrar?siguiente=${encodeURIComponent(next)}`}>Entrar</Link>
        </p>
      </div>
    </main>
  )
}
