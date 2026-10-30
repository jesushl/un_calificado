import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

import { api, type ServiceRequest } from "../api/client"
import { PROJECT_STATUS, RULER_FILL, tradeLabel } from "../catalog"
import { useAuth } from "../auth/AuthContext"
import { Mark } from "../brand/Mark"

export function HomePage() {
  const { user } = useAuth()
  if (user?.role === "ADMINISTRADOR") return <AdminHome />
  if (user?.role === "PROVEEDOR") return <Inbox title="Solicitudes" emptyTitle="No tienes solicitudes nuevas" emptyText="Cuando un cliente de tu zona pida tu oficio, te aparece aquí. Mientras, mantén tu agenda al día." />
  return <Inbox title="Tus proyectos" emptyTitle="Aún no tienes proyectos" emptyText="Cuéntanos qué hace falta en tu casa. Con tu colonia y un par de datos, los proveedores verificados de tu zona pueden mandarte propuesta." create />
}

function Inbox({
  title,
  emptyTitle,
  emptyText,
  create = false,
}: {
  title: string
  emptyTitle: string
  emptyText: string
  create?: boolean
}) {
  const [items, setItems] = useState<ServiceRequest[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listRequests()
      .then((payload) => setItems(payload.items))
      .catch((caught: Error) => setError(caught.message))
  }, [])

  return (
    <section className="stack stack--lg">
      <div className="cota">
        <p className="eyebrow">{title}</p>
        <h1>{title}</h1>
      </div>
      {create ? (
        <p>
          <Link className="btn btn-primary" to="/nuevo">
            Crear mi primer proyecto
          </Link>
        </p>
      ) : null}
      {error ? (
        <p className="alert alert--danger" role="alert">
          {error}
        </p>
      ) : null}
      {items.length === 0 && !error ? (
        <section className="empty">
          <div className="empty-inner">
            <Mark className="empty-figure wordmark-mark" />
            <div className="empty-body">
              <h2 className="empty-title">{emptyTitle}</h2>
              <p className="empty-text">{emptyText}</p>
              {create ? (
                <div className="empty-actions">
                  <Link className="btn btn-primary" to="/nuevo">
                    Crear mi primer proyecto
                  </Link>
                </div>
              ) : null}
            </div>
          </div>
        </section>
      ) : (
        <ul className="stack">
          {items.map((item) => (
            <li key={item.id}>
              <Link to={`/proyectos/${item.id}`} className="ficha" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
                <p className="eyebrow">{tradeLabel(item.trade)}</p>
                <h2>{item.expectedOutcome}</h2>
                <p>{item.approximateZone}</p>
                <span className="status" data-status={item.status}>
                  {PROJECT_STATUS[item.status] ?? item.status}
                </span>
                <div className="ruler-wrap">
                  <div
                    className="ruler"
                    style={{ ["--p" as string]: (RULER_FILL[item.status] ?? 0) / 100 }}
                    aria-hidden="true"
                  />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function AdminHome() {
  const month = new Date().toISOString().slice(0, 7)
  const [percent, setPercent] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .availabilityReport(month)
      .then((report) => setPercent(report.availabilityPercent))
      .catch((caught: Error) => setError(caught.message))
  }, [month])

  return (
    <section className="stack stack--lg">
      <div className="cota">
        <p className="eyebrow">Operación</p>
        <h1>Disponibilidad del mes</h1>
      </div>
      {error ? (
        <p className="alert alert--danger" role="alert">
          {error}
        </p>
      ) : (
        <p>
          {month}: {percent ?? "…"} % de disponibilidad.
        </p>
      )}
      <p>Aquí llegan las solicitudes de acceso, rectificación, cancelación y oposición, y los documentos por verificar.</p>
    </section>
  )
}
