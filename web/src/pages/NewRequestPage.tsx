import { useState, type FormEvent } from "react"
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom"

import { api, ApiError } from "../api/client"
import { TRADES, userDiscovery } from "../catalog"
import { useAuth } from "../auth/AuthContext"

export function NewRequestPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const preferredProvider = params.get("proveedor")
  const [outcome, setOutcome] = useState("")
  const [trade, setTrade] = useState(params.get("oficio") || "albanileria")
  const [zone, setZone] = useState(userDiscovery(user).zone ?? "")
  const [date, setDate] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  if (user?.role !== "CLIENTE") return <Navigate to="/" replace />

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!outcome.trim()) {
      setError("Escribe qué quieres que quede listo.")
      return
    }
    if (!zone.trim()) {
      setError("Escribe en qué colonia estás.")
      return
    }
    setPending(true)
    setError(null)
    try {
      const created = preferredProvider
        ? await api.contactProvider(preferredProvider, {
            expectedOutcome: outcome.trim(),
            approximateZone: zone.trim(),
            trade,
          })
        : await api.createRequest({
            expectedOutcome: outcome.trim(),
            trade,
            approximateZone: zone.trim(),
            desiredDate: date || undefined,
            description: description.trim() || undefined,
            manualCapture: true,
          })
      navigate(`/proyectos/${created.id}`)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "No pudimos conectar. Revisa tu internet y vuelve a intentar.")
    } finally {
      setPending(false)
    }
  }

  return (
    <section className="stack stack--lg">
      <div className="cota">
        <p className="eyebrow">Nuevo proyecto</p>
        <h1>Cuéntanos qué necesitas</h1>
      </div>
      {error ? (
        <p className="alert alert--danger" role="alert">
          {error}
        </p>
      ) : null}
      <form className="stack" onSubmit={(event) => void onSubmit(event)}>
        <label className="field">
          <span className="field-label">¿Qué quieres que quede listo?</span>
          <textarea
            className="input"
            name="expectedOutcome"
            rows={3}
            value={outcome}
            onChange={(event) => setOutcome(event.target.value)}
          />
          <span className="field-hint">Ej. “Que no gotee el lavabo del baño de visitas.”</span>
        </label>
        <label className="field">
          <span className="field-label">¿Qué oficio necesitas?</span>
          <select className="input" name="trade" value={trade} onChange={(event) => setTrade(event.target.value)}>
            {TRADES.map((item) => (
              <option key={item.id} value={item.id}>
                {item.key} · {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">¿En qué colonia estás?</span>
          <input
            className="input"
            name="approximateZone"
            value={zone}
            onChange={(event) => setZone(event.target.value)}
          />
          <span className="field-hint">Con la colonia basta. Tu calle y número se quedan contigo.</span>
        </label>
        <label className="field">
          <span className="field-label">¿Para cuándo lo quieres?</span>
          <input
            className="input"
            name="desiredDate"
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
          />
        </label>
        <label className="field">
          <span className="field-label">Detalles</span>
          <textarea
            className="input"
            name="description"
            rows={4}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <span className="field-hint">Medidas, materiales, desde cuándo pasa. No pongas teléfonos: los quitamos.</span>
        </label>
        <p>Tu domicilio exacto nunca se publica.</p>
        <div className="cluster">
          <button className="btn btn-primary" type="submit" disabled={pending}>
            {pending ? "Guardando cambios…" : "Guardar borrador"}
          </button>
          <Link className="btn btn-ghost" to="/proyectos">
            Seguir editando
          </Link>
        </div>
      </form>
    </section>
  )
}
