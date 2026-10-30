import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"

import { api, type ExploreProvider, type ExploreWork } from "../api/client"
import { initials, tradeKey, tradeLabel } from "../catalog"
import { ContactCta } from "../components/ContactCta"

export function ProviderPage() {
  const { providerId = "" } = useParams()
  const [provider, setProvider] = useState<ExploreProvider | null>(null)
  const [works, setWorks] = useState<ExploreWork[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.publicProvider(providerId), api.publicWorks()])
      .then(([ficha, gallery]) => {
        setProvider(ficha)
        setWorks(gallery.items.filter((item) => item.provider.id === providerId))
      })
      .catch((caught: Error) => setError(caught.message))
  }, [providerId])

  if (error) {
    return (
      <p className="alert alert--danger" role="alert">
        {error} <Link to="/">Volver al índice</Link>
      </p>
    )
  }
  if (!provider) return <p>Cargando ficha…</p>

  return (
    <article className="stack stack--lg">
      <p>
        <Link to="/">Volver al índice</Link>
      </p>
      <div className="ficha">
        <div className="ficha-inner">
          <div
            className={provider.modality === "ORGANIZACION" ? "ficha-id ficha-id--org" : "ficha-id"}
            aria-hidden="true"
          >
            {initials(provider.name)}
          </div>
          <div className="ficha-title">
            <p className="eyebrow">{provider.verified ? "Verificado" : "Declarado"}</p>
            <h1 className="ficha-name" style={{ fontSize: "var(--text-xl)" }}>
              {provider.name}
            </h1>
            <p className="ficha-meta">Zona aproximada: {provider.coverage.join(", ")}</p>
          </div>
          <div className="ficha-trades">
            {provider.trades.map((trade) => (
              <span className="chip" key={trade}>
                <span className="chip-key">{tradeKey(trade)}</span>
                {tradeLabel(trade)}
              </span>
            ))}
          </div>
          <dl className="ficha-facts">
            <div className="ficha-fact">
              <dt>Calificación</dt>
              <dd>
                {provider.rating.average.toFixed(1)} <small>({provider.rating.count})</small>
              </dd>
            </div>
            <div className="ficha-fact">
              <dt>Años</dt>
              <dd>{provider.experienceYears}</dd>
            </div>
          </dl>
          <div className="ficha-actions">
            <ContactCta provider={provider} />
          </div>
        </div>
      </div>
      <p>Tu domicilio exacto nunca se publica. El contacto va por UnCalificado, no por teléfono.</p>
      {works.length ? (
        <section className="stack">
          <h2>Proyectos realizados</h2>
          <ul className="obra-muro">
            {works.map((work) => (
              <li key={work.id}>
                <figure className="obra-foto">
                  <img
                    src={work.downloadUrl}
                    alt={`${work.expectedOutcome}. Zona aproximada: ${work.approximateZone}.`}
                  />
                  <figcaption className="obra-caption">
                    <strong>{work.expectedOutcome}</strong>
                    <span>Zona aproximada: {work.approximateZone}</span>
                  </figcaption>
                </figure>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <p>Este calificado todavía no publica fotos de obra concluida.</p>
      )}
    </article>
  )
}
