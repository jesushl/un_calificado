import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

import { api, type Appointment } from "../api/client"
import { useAuth } from "../auth/AuthContext"
import { APPOINTMENT_STATUS, formatDateTime, formatMxn } from "../catalog"

export function AgendaPage() {
  const { user } = useAuth()
  const [items, setItems] = useState<Appointment[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listAppointments()
      .then((payload) => setItems(payload.items))
      .catch((caught: Error) => setError(caught.message))
  }, [])

  if (user?.role !== "PROVEEDOR") {
    return (
      <p>
        La agenda es para prestadores. <Link to="/proyectos">Ir a proyectos</Link>
      </p>
    )
  }

  return (
    <section className="stack stack--lg" data-testid="agenda-page">
      <div className="cota">
        <p className="eyebrow">Agenda</p>
        <h1>Tus citas</h1>
      </div>
      <p>Visitas y ejecuciones que tienes con clientes. El domicilio exacto solo aparece si el cliente lo autorizó en el proyecto.</p>
      {error ? (
        <p className="alert alert--danger" role="alert">
          {error}
        </p>
      ) : null}
      {items.length === 0 && !error ? (
        <p>No tienes citas todavía. Cuando aceptes una solicitud, propone visita desde el proyecto.</p>
      ) : (
        <ul className="stack">
          {items.map((item) => (
            <li key={item.id}>
              <Link
                to={`/proyectos/${item.requestId}`}
                className="ficha"
                style={{ textDecoration: "none", color: "inherit", display: "block" }}
                data-testid={`agenda-item-${item.id}`}
              >
                <p className="eyebrow">{item.isVisit ? "Visita" : "Ejecución"}</p>
                <h2>{formatDateTime(item.startsAt)}</h2>
                <p>
                  {formatMxn(item.costMxn)} · {APPOINTMENT_STATUS[item.status] ?? item.status}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
