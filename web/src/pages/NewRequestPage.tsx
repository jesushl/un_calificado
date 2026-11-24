import { useEffect, useMemo, useState, type FormEvent } from "react"
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom"

import { api, ApiError, type ExploreProvider } from "../api/client"
import { isPastDate, todayIsoMexico, TRADES, tradeKey, tradeLabel, userDiscovery } from "../catalog"
import { useAuth } from "../auth/AuthContext"

export function NewRequestPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const preferredProvider = params.get("proveedor")
  const oficioFromUrl = params.get("oficio") || ""
  const [outcome, setOutcome] = useState("")
  const [trade, setTrade] = useState(oficioFromUrl || "albanileria")
  const [zone, setZone] = useState(userDiscovery(user).zone ?? "")
  const [date, setDate] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [provider, setProvider] = useState<ExploreProvider | null>(null)
  const [loadingProvider, setLoadingProvider] = useState(Boolean(preferredProvider))

  const tradeOptions = useMemo(() => {
    if (provider?.trades?.length) {
      return TRADES.filter((item) => provider.trades.includes(item.id))
    }
    return [...TRADES]
  }, [provider])

  useEffect(() => {
    if (!preferredProvider) {
      setProvider(null)
      setLoadingProvider(false)
      return
    }
    setLoadingProvider(true)
    api
      .publicProvider(preferredProvider)
      .then((ficha) => {
        setProvider(ficha)
        const allowed = ficha.trades
        if (oficioFromUrl && allowed.includes(oficioFromUrl)) {
          setTrade(oficioFromUrl)
        } else if (allowed.length) {
          setTrade(allowed[0])
        }
      })
      .catch((caught: Error) => setError(caught.message))
      .finally(() => setLoadingProvider(false))
  }, [preferredProvider, oficioFromUrl])

  if (user?.role !== "CLIENTE") return <Navigate to="/" replace />

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const nextOutcome = String(data.get("expectedOutcome") || outcome).trim()
    const nextZone = String(data.get("approximateZone") || zone).trim()
    const nextTrade = String(data.get("trade") || trade)
    const nextDate = String(data.get("desiredDate") || date)
    const nextDescription = String(data.get("description") || description).trim()
    if (!nextOutcome) {
      setError("Escribe qué quieres que quede listo.")
      return
    }
    if (!nextZone) {
      setError("Escribe en qué colonia estás.")
      return
    }
    if (!nextDate) {
      setError("Indica para cuándo lo quieres.")
      return
    }
    if (isPastDate(nextDate)) {
      setError("La fecha tiene que ser hoy o una fecha futura. No uses fechas del pasado.")
      return
    }
    if (provider && !provider.trades.includes(nextTrade)) {
      setError("Ese oficio no lo ofrece este calificado. Elige uno de su ficha.")
      return
    }
    setPending(true)
    setError(null)
    try {
      const created = preferredProvider
        ? await api.contactProvider(preferredProvider, {
            expectedOutcome: nextOutcome,
            approximateZone: nextZone,
            trade: nextTrade,
            desiredDate: nextDate || undefined,
            description: nextDescription || undefined,
          })
        : await api.createRequest({
            expectedOutcome: nextOutcome,
            trade: nextTrade,
            approximateZone: nextZone,
            desiredDate: nextDate || undefined,
            description: nextDescription || undefined,
            manualCapture: true,
          })
      navigate(`/proyectos/${created.id}`)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "No pudimos conectar. Revisa tu internet y vuelve a intentar.")
    } finally {
      setPending(false)
    }
  }

  const lockedTrade = provider && tradeOptions.length === 1 ? tradeOptions[0] : null

  return (
    <section className="stack stack--lg">
      <div className="cota">
        <p className="eyebrow">Nuevo proyecto</p>
        <h1>Cuéntanos qué necesitas</h1>
      </div>
      {provider ? (
        <p data-testid="contact-provider-context">
          Cotización con <strong>{provider.name}</strong>
          {oficioFromUrl ? (
            <>
              {" "}
              · oficio de la obra: <strong>{tradeLabel(oficioFromUrl)}</strong>
            </>
          ) : null}
          . Solo puedes pedir oficios que este calificado declara.
        </p>
      ) : null}
      {error ? (
        <p className="alert alert--danger" role="alert">
          {error}
        </p>
      ) : null}
      {loadingProvider ? <p>Cargando oficios del calificado…</p> : null}
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
          {lockedTrade ? (
            <>
              <input type="hidden" name="trade" value={lockedTrade.id} />
              <p className="input" data-testid="trade-locked" style={{ margin: 0 }}>
                <span className="chip-key">{tradeKey(lockedTrade.id)}</span> {lockedTrade.label}
              </p>
              <span className="field-hint">
                Este calificado solo ofrece este oficio; viene de la obra o de su ficha.
              </span>
            </>
          ) : (
            <>
              <select
                className="input"
                name="trade"
                value={trade}
                onChange={(event) => setTrade(event.target.value)}
                data-testid="trade-select"
              >
                {tradeOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.key} · {item.label}
                  </option>
                ))}
              </select>
              <span className="field-hint">
                {provider
                  ? "Solo aparecen los oficios que este calificado tiene registrados."
                  : "Elige el oficio del catálogo que mejor describe el trabajo."}
              </span>
            </>
          )}
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
            min={todayIsoMexico()}
            value={date}
            onChange={(event) => setDate(event.target.value)}
            required
          />
          <span className="field-hint">Elige hoy o un día adelante. No se aceptan fechas pasadas.</span>
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
          <button className="btn btn-primary" type="submit" disabled={pending || loadingProvider}>
            {pending ? "Guardando cambios…" : "Guardar borrador"}
          </button>
          <Link className="btn btn-ghost" to={preferredProvider ? `/calificados/${preferredProvider}` : "/proyectos"}>
            Volver
          </Link>
        </div>
      </form>
    </section>
  )
}
