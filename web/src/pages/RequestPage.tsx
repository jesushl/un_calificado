import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"

import { api, ApiError, type ServiceRequest } from "../api/client"
import { PROJECT_STATUS, RULER_FILL, tradeLabel, zoneClass } from "../catalog"

export function RequestPage() {
  const { requestId = "" } = useParams()
  const [item, setItem] = useState<ServiceRequest | null>(null)
  const [privacy, setPrivacy] = useState<{
    visibility: string
    neighborhood?: string
    exactAddress?: string | null
  } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    Promise.all([api.getRequest(requestId), api.getPrivacy(requestId)])
      .then(([request, location]) => {
        setItem(request)
        setPrivacy(location)
      })
      .catch((caught: Error) => setError(caught.message))
  }, [requestId])

  async function confirm() {
    setPending(true)
    try {
      setItem(await api.confirmRequest(requestId))
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "No pudimos conectar.")
    } finally {
      setPending(false)
    }
  }

  if (error && !item) {
    return (
      <p className="alert alert--danger" role="alert">
        {error} <Link to="/proyectos">Volver a mis proyectos</Link>
      </p>
    )
  }
  if (!item) return <p>Cargando proyecto…</p>

  const visibility = privacy?.visibility ?? "ZONA_APROXIMADA"
  const authorized = visibility === "DOMICILIO_AUTORIZADO"

  return (
    <article className="stack stack--lg">
      <div className="cota">
        <p className="eyebrow">{tradeLabel(item.trade)}</p>
        <h1>{item.expectedOutcome}</h1>
      </div>
      <span className="status" data-status={item.status}>
        {PROJECT_STATUS[item.status] ?? item.status}
      </span>
      <div className="ruler-wrap">
        <div className="ruler" style={{ ["--p" as string]: (RULER_FILL[item.status] ?? 0) / 100 }} />
      </div>
      {item.description ? <p>{item.description}</p> : null}
      <div className="zone-inner">
        <div className={zoneClass(visibility)}>
          <p className="eyebrow">
            {authorized ? "Domicilio exacto" : visibility === "OCULTO" ? "Sin ubicación visible" : "Zona aproximada"}
          </p>
          <p>{authorized ? privacy?.exactAddress : privacy?.neighborhood || item.approximateZone}</p>
          <p>
            {authorized
              ? "El cliente autorizó que veas su domicilio para este proyecto. Úsalo solo para llegar a la cita."
              : "Esto es lo que ven los proveedores mientras revisan tu solicitud. Tu calle y número se quedan contigo."}
          </p>
        </div>
      </div>
      {error ? (
        <p className="alert alert--danger" role="alert">
          {error}
        </p>
      ) : null}
      {item.status === "BORRADOR" ? (
        <button className="btn btn-primary" type="button" disabled={pending} onClick={() => void confirm()}>
          {pending ? "Enviando solicitud…" : "Confirmar proyecto"}
        </button>
      ) : null}
      <p>
        <Link to="/">Volver a mis proyectos</Link>
      </p>
    </article>
  )
}
