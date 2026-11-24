import { useEffect, useState, type FormEvent } from "react"
import { Link, useParams } from "react-router-dom"

import {
  api,
  ApiError,
  type Appointment,
  type ProjectMessage,
  type Proposal,
  type ServiceRequest,
} from "../api/client"
import { useAuth } from "../auth/AuthContext"
import {
  APPOINTMENT_STATUS,
  formatDateTime,
  formatMxn,
  PROJECT_STATUS,
  PROPOSAL_STATUS,
  RULER_FILL,
  tradeLabel,
  zoneClass,
} from "../catalog"

function toLocalInput(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ""
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function fromLocalInput(value: string): string {
  return new Date(value).toISOString()
}

export function RequestPage() {
  const { requestId = "" } = useParams()
  const { user } = useAuth()
  const [item, setItem] = useState<ServiceRequest | null>(null)
  const [privacy, setPrivacy] = useState<{
    visibility: string
    neighborhood?: string
    exactAddress?: string | null
  } | null>(null)
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [messages, setMessages] = useState<ProjectMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [messageText, setMessageText] = useState("")
  const [visitStarts, setVisitStarts] = useState("")
  const [visitEnds, setVisitEnds] = useState("")
  const [visitCost, setVisitCost] = useState("350")
  const [workDescription, setWorkDescription] = useState("")
  const [labor, setLabor] = useState("1000")
  const [materialsCost, setMaterialsCost] = useState("200")
  const [extras, setExtras] = useState("0")
  const [providerAccepted, setProviderAccepted] = useState(false)
  const [evalScore, setEvalScore] = useState("5")
  const [evalComment, setEvalComment] = useState("")
  const [evaluated, setEvaluated] = useState(false)
  const [rejectReason, setRejectReason] = useState("")

  const isProvider = user?.role === "PROVEEDOR"
  const isClient = user?.role === "CLIENTE"

  async function reload() {
    const [request, location, appts, props] = await Promise.all([
      api.getRequest(requestId),
      api.getPrivacy(requestId),
      api.listAppointments(requestId),
      api.listProposals(requestId),
    ])
    setItem(request)
    setPrivacy(location)
    setAppointments(appts.items)
    setProposals(props.items)
    if (appts.items.some((row) => row.status === "PENDIENTE" || row.status === "CONFIRMADA")) {
      const thread = await api.listMessages(requestId)
      setMessages(thread.items)
    } else {
      setMessages([])
    }
  }

  useEffect(() => {
    setEvaluated(false)
    setProviderAccepted(false)
    reload().catch((caught: Error) => setError(caught.message))
  }, [requestId])

  async function run(action: () => Promise<void>) {
    setPending(true)
    setError(null)
    try {
      await action()
      await reload()
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
  const canMessage = appointments.some(
    (row) => row.status === "PENDIENTE" || row.status === "CONFIRMADA",
  )
  const hasAcceptedProposal = proposals.some((row) => row.status === "ACEPTADA")
  const laborNum = Number(labor) || 0
  const materialsNum = Number(materialsCost) || 0
  const extrasNum = Number(extras) || 0
  const proposalTotal = laborNum + materialsNum + extrasNum
  const evalSubject = isClient ? "PROVEEDOR" : "CLIENTE"

  return (
    <article className="stack stack--lg">
      <div className="cota">
        <p className="eyebrow">{tradeLabel(item.trade)}</p>
        <h1>{item.expectedOutcome}</h1>
      </div>
      <span className="status" data-status={item.status} data-testid="project-status">
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

      {isClient && item.status === "BORRADOR" ? (
        <button
          className="btn btn-primary"
          type="button"
          disabled={pending}
          data-testid="confirm-request"
          onClick={() => void run(async () => { await api.confirmRequest(requestId) })}
        >
          {pending ? "Enviando solicitud…" : "Confirmar proyecto"}
        </button>
      ) : null}

      {isProvider &&
      item.status === "CONFIRMADA" &&
      item.selectedProviderId &&
      !providerAccepted &&
      appointments.length === 0 &&
      proposals.length === 0 ? (
        <section className="stack" data-testid="provider-decision">
          <h2>¿Aceptas esta solicitud?</h2>
          <p>Si aceptas, puedes proponer visita o mandar presupuesto directo.</p>
          <div className="cluster">
            <button
              className="btn btn-primary"
              type="button"
              disabled={pending}
              data-testid="accept-request"
              onClick={() =>
                void run(async () => {
                  await api.providerDecision(requestId, "ACEPTAR")
                  setProviderAccepted(true)
                })
              }
            >
              Aceptar solicitud
            </button>
            <button
              className="btn btn-ghost"
              type="button"
              disabled={pending}
              data-testid="reject-request"
              onClick={() => void run(async () => { await api.providerDecision(requestId, "RECHAZAR") })}
            >
              Rechazar
            </button>
          </div>
        </section>
      ) : null}

      <section className="stack" data-testid="appointments-section">
        <h2>Citas</h2>
        {appointments.length === 0 ? <p>Aún no hay citas en este proyecto.</p> : null}
        <ul className="stack">
          {appointments.map((appt) => (
            <li key={appt.id} className="ficha" data-testid={`appointment-${appt.id}`}>
              <p className="eyebrow">{appt.isVisit ? "Visita" : "Ejecución"}</p>
              <p>
                {formatDateTime(appt.startsAt)} — {formatDateTime(appt.endsAt)}
              </p>
              <p>
                {formatMxn(appt.costMxn)} · {APPOINTMENT_STATUS[appt.status] ?? appt.status}
              </p>
              {isClient && appt.status === "PENDIENTE" && !appt.confirmedByClient ? (
                <button
                  className="btn btn-primary btn-sm"
                  type="button"
                  disabled={pending}
                  data-testid="confirm-appointment"
                  onClick={() =>
                    void run(async () => {
                      await api.updateAppointment(appt.id, { confirmedByClient: true })
                    })
                  }
                >
                  Confirmar cita
                </button>
              ) : null}
            </li>
          ))}
        </ul>
        {isProvider && item.selectedProviderId ? (
          <form
            className="stack"
            data-testid="propose-visit-form"
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault()
              const data = new FormData(event.currentTarget)
              const starts = String(data.get("visitStarts") || visitStarts)
              const ends = String(data.get("visitEnds") || visitEnds)
              const cost = String(data.get("visitCost") || visitCost)
              if (!starts || !ends) {
                setError("Indica inicio y fin de la cita.")
                return
              }
              void run(async () => {
                await api.createAppointment({
                  requestId,
                  startsAt: fromLocalInput(starts),
                  endsAt: fromLocalInput(ends),
                  costMxn: Number(cost) || 0,
                  confirmedByProvider: true,
                  isVisit: true,
                })
                setVisitStarts("")
                setVisitEnds("")
              })
            }}
          >
            <h3>Proponer visita</h3>
            <label className="field">
              <span className="field-label">Inicio</span>
              <input
                className="input"
                type="datetime-local"
                name="visitStarts"
                value={visitStarts}
                onChange={(event) => setVisitStarts(event.target.value)}
              />
            </label>
            <label className="field">
              <span className="field-label">Fin</span>
              <input
                className="input"
                type="datetime-local"
                name="visitEnds"
                value={visitEnds || (visitStarts ? toLocalInput(new Date(new Date(visitStarts).getTime() + 2 * 3600_000).toISOString()) : "")}
                onChange={(event) => setVisitEnds(event.target.value)}
              />
            </label>
            <label className="field">
              <span className="field-label">Costo de visita (MXN)</span>
              <input
                className="input"
                type="number"
                min={0}
                name="visitCost"
                value={visitCost}
                onChange={(event) => setVisitCost(event.target.value)}
              />
            </label>
            <button className="btn btn-primary" type="submit" disabled={pending}>
              Enviar propuesta de visita
            </button>
          </form>
        ) : null}
      </section>

      <section className="stack" data-testid="proposals-section">
        <h2>Presupuesto</h2>
        {proposals.length === 0 ? <p>Todavía no hay presupuesto en este proyecto.</p> : null}
        <ul className="stack">
          {proposals.map((proposal) => (
            <li key={proposal.id} className="ficha" data-testid={`proposal-${proposal.id}`}>
              <p className="eyebrow">Versión {proposal.version}</p>
              <h3>{formatMxn(proposal.totalMxn)}</h3>
              <p>{proposal.workDescription}</p>
              <span className="status" data-status={proposal.status}>
                {PROPOSAL_STATUS[proposal.status] ?? proposal.status}
              </span>
              {isClient && proposal.status === "ENVIADA" ? (
                <div className="cluster">
                  <button
                    className="btn btn-primary btn-sm"
                    type="button"
                    disabled={pending}
                    data-testid="accept-proposal"
                    onClick={() =>
                      void run(async () => {
                        await api.decideProposal(proposal.id, "ACEPTAR")
                      })
                    }
                  >
                    Aceptar presupuesto
                  </button>
                  <button
                    className="btn btn-ghost btn-sm"
                    type="button"
                    disabled={pending}
                    onClick={() =>
                      void run(async () => {
                        await api.decideProposal(proposal.id, "RECHAZAR")
                      })
                    }
                  >
                    Rechazar
                  </button>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
        {isProvider && item.selectedProviderId ? (
          <form
            className="stack"
            data-testid="create-proposal-form"
            onSubmit={(event: FormEvent) => {
              event.preventDefault()
              if (!workDescription.trim()) {
                setError("Describe el trabajo del presupuesto.")
                return
              }
              void run(async () => {
                await api.createProposal({
                  requestId,
                  workDescription: workDescription.trim(),
                  laborSubtotalMxn: laborNum,
                  materials:
                    materialsNum > 0
                      ? [
                          {
                            description: "Materiales",
                            quantity: 1,
                            unit: "lote",
                            unitPriceMxn: materialsNum,
                            subtotalMxn: materialsNum,
                          },
                        ]
                      : [],
                  additionalCostsMxn: extrasNum,
                  totalMxn: proposalTotal,
                })
                setWorkDescription("")
              })
            }}
          >
            <h3>Enviar presupuesto</h3>
            <p>Puedes mandarlo sin visita si ya conoces el alcance.</p>
            <label className="field">
              <span className="field-label">Qué incluye el trabajo</span>
              <textarea
                className="input"
                name="workDescription"
                rows={3}
                value={workDescription}
                onChange={(event) => setWorkDescription(event.target.value)}
              />
            </label>
            <label className="field">
              <span className="field-label">Mano de obra (MXN)</span>
              <input
                className="input"
                type="number"
                min={0}
                name="labor"
                value={labor}
                onChange={(event) => setLabor(event.target.value)}
              />
            </label>
            <label className="field">
              <span className="field-label">Materiales (MXN)</span>
              <input
                className="input"
                type="number"
                min={0}
                name="materials"
                value={materialsCost}
                onChange={(event) => setMaterialsCost(event.target.value)}
              />
            </label>
            <label className="field">
              <span className="field-label">Extras (MXN)</span>
              <input
                className="input"
                type="number"
                min={0}
                name="extras"
                value={extras}
                onChange={(event) => setExtras(event.target.value)}
              />
            </label>
            <p>Total: {formatMxn(proposalTotal)}</p>
            <button className="btn btn-primary" type="submit" disabled={pending}>
              Enviar presupuesto
            </button>
          </form>
        ) : null}
      </section>

      <section className="stack" data-testid="work-section">
        <h2>Avance del trabajo</h2>
        {!hasAcceptedProposal ? (
          <p>El trabajo arranca cuando el cliente acepta el presupuesto.</p>
        ) : null}
        {hasAcceptedProposal && item.status === "CONFIRMADA" ? (
          <p>Falta confirmar una cita para programar el trabajo.</p>
        ) : null}
        {isProvider && item.status === "PROGRAMADO" && hasAcceptedProposal ? (
          <div className="cluster">
            <button
              className="btn btn-primary"
              type="button"
              disabled={pending}
              data-testid="start-work"
              onClick={() =>
                void run(async () => {
                  await api.updateRequestStatus(requestId, "EN_PROCESO")
                })
              }
            >
              Iniciar trabajo
            </button>
          </div>
        ) : null}
        {isProvider && item.status === "EN_PROCESO" ? (
          <div className="cluster">
            <button
              className="btn btn-primary"
              type="button"
              disabled={pending}
              data-testid="finish-work"
              onClick={() =>
                void run(async () => {
                  await api.updateRequestStatus(requestId, "TERMINADO")
                })
              }
            >
              Marcar terminado
            </button>
          </div>
        ) : null}
        {isClient && item.status === "TERMINADO" ? (
          <div className="stack">
            <p>El prestador marcó el trabajo como terminado. ¿Confirmas el cierre?</p>
            <div className="cluster">
              <button
                className="btn btn-primary"
                type="button"
                disabled={pending}
                data-testid="conclude-work"
                onClick={() =>
                  void run(async () => {
                    await api.updateRequestStatus(requestId, "CONCLUIDO")
                  })
                }
              >
                Confirmar cierre
              </button>
            </div>
            <label className="field">
              <span className="field-label">Si aún no queda listo, di qué falta</span>
              <input
                className="input"
                name="rejectReason"
                value={rejectReason}
                onChange={(event) => setRejectReason(event.target.value)}
                data-testid="reject-close-reason"
              />
            </label>
            <button
              className="btn btn-ghost"
              type="button"
              disabled={pending || !rejectReason.trim()}
              data-testid="reject-close"
              onClick={() =>
                void run(async () => {
                  await api.updateRequestStatus(requestId, "EN_PROCESO", rejectReason.trim())
                  setRejectReason("")
                })
              }
            >
              Todavía no está listo
            </button>
          </div>
        ) : null}
        {item.status === "CONCLUIDO" ? (
          <p data-testid="work-closed">Proyecto cerrado. Ya pueden evaluarse mutuamente.</p>
        ) : null}
      </section>

      {item.status === "CONCLUIDO" ? (
        <section className="stack" data-testid="evaluation-section">
          <h2>{isClient ? "Evalúa al prestador" : "Evalúa al cliente"}</h2>
          {evaluated ? (
            <p data-testid="evaluation-done">Gracias. Tu evaluación quedó registrada.</p>
          ) : (
            <form
              className="stack"
              onSubmit={(event: FormEvent<HTMLFormElement>) => {
                event.preventDefault()
                const data = new FormData(event.currentTarget)
                const score = Number(data.get("score") || evalScore)
                const comment = String(data.get("comment") || evalComment).trim()
                void run(async () => {
                  try {
                    await api.createEvaluation(requestId, {
                      subjectType: evalSubject,
                      score,
                      quality: score,
                      comment: comment || undefined,
                    })
                    setEvaluated(true)
                  } catch (caught) {
                    if (caught instanceof ApiError && caught.status === 409) {
                      setEvaluated(true)
                      return
                    }
                    throw caught
                  }
                })
              }}
            >
              <label className="field">
                <span className="field-label">Calificación (1 a 5)</span>
                <input
                  className="input"
                  type="number"
                  min={1}
                  max={5}
                  name="score"
                  value={evalScore}
                  onChange={(event) => setEvalScore(event.target.value)}
                  data-testid="evaluation-score"
                />
              </label>
              <label className="field">
                <span className="field-label">Comentario (opcional)</span>
                <textarea
                  className="input"
                  name="comment"
                  rows={3}
                  value={evalComment}
                  onChange={(event) => setEvalComment(event.target.value)}
                  data-testid="evaluation-comment"
                />
              </label>
              <button className="btn btn-primary" type="submit" disabled={pending} data-testid="submit-evaluation">
                Enviar evaluación
              </button>
            </form>
          )}
        </section>
      ) : null}

      <section className="stack" data-testid="messages-section">
        <h2>Mensajes</h2>
        {!canMessage ? (
          <p>El canal se abre cuando hay una cita pendiente o confirmada.</p>
        ) : (
          <>
            <ul className="stack" data-testid="message-list">
              {messages.map((message) => (
                <li key={message.id}>
                  <p>{message.content}</p>
                  <p className="eyebrow">{formatDateTime(message.sentAt)}</p>
                </li>
              ))}
            </ul>
            <form
              className="stack"
              onSubmit={(event: FormEvent) => {
                event.preventDefault()
                if (!messageText.trim()) return
                void run(async () => {
                  await api.sendMessage(requestId, messageText.trim())
                  setMessageText("")
                })
              }}
            >
              <label className="field">
                <span className="field-label">Escribe un mensaje</span>
                <textarea
                  className="input"
                  name="message"
                  rows={3}
                  value={messageText}
                  onChange={(event) => setMessageText(event.target.value)}
                  data-testid="message-input"
                />
                <span className="field-hint">Sin teléfonos: el canal es solo del proyecto.</span>
              </label>
              <button className="btn btn-primary" type="submit" disabled={pending} data-testid="send-message">
                Enviar
              </button>
            </form>
          </>
        )}
      </section>

      <p>
        <Link to="/proyectos">Volver a mis proyectos</Link>
      </p>
    </article>
  )
}
