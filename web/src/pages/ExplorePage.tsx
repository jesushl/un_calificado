import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"

import { api, type ExploreProvider, type ExploreWork } from "../api/client"
import { TRADES, initials, tradeKey, tradeLabel } from "../catalog"
import { ContactCta } from "../components/ContactCta"

export function ExplorePage() {
  const [params, setParams] = useSearchParams()
  const oficio = params.get("oficio") || ""
  const [providers, setProviders] = useState<ExploreProvider[]>([])
  const [works, setWorks] = useState<ExploreWork[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setError(null)
    setLoading(true)
    Promise.all([api.popularProviders(oficio || undefined), api.publicWorks(oficio || undefined)])
      .then(([popular, gallery]) => {
        setProviders(popular.items)
        setWorks(gallery.items)
      })
      .catch((caught: Error) => setError(caught.message))
      .finally(() => setLoading(false))
  }, [oficio])

  function selectTrade(id: string) {
    const next = new URLSearchParams(params)
    if (!id || id === oficio) next.delete("oficio")
    else next.set("oficio", id)
    setParams(next, { replace: true })
  }

  return (
    <div className="stack stack--lg">
      <section className="hero plano">
        <p className="eyebrow">Índice</p>
        <h1>Quien sí sabe, a la vuelta de tu casa.</h1>
        <p>
          Mira calificados y fotos de obra terminada sin crear cuenta. El domicilio exacto no se
          publica. Para escribirle a alguien, entra.
        </p>
      </section>

      <div className="cluster" role="group" aria-label="Filtrar por oficio">
        {TRADES.map((trade) => (
          <button
            key={trade.id}
            type="button"
            className="chip"
            aria-pressed={oficio === trade.id}
            onClick={() => selectTrade(trade.id)}
          >
            <span className="chip-key">{trade.key}</span>
            {trade.label}
          </button>
        ))}
      </div>

      {error ? (
        <p className="alert alert--danger" role="alert">
          {error}
        </p>
      ) : null}

      <section className="stack" aria-labelledby="obras-titulo">
        <div className="cota">
          <p className="eyebrow">Obra hecha</p>
          <h2 id="obras-titulo">Fotos de proyectos realizados</h2>
        </div>
        {loading ? (
          <p>Cargando fotos de obra…</p>
        ) : works.length === 0 && !error ? (
          <p>Todavía no hay fotos de obra para mostrar. Cuando un proyecto concluye, aparece aquí.</p>
        ) : (
          <ul className="obra-muro">
            {works.map((work) => (
              <li key={work.id}>
                <Link className="obra-foto" to={`/calificados/${work.provider.id}`}>
                  <img
                    src={work.downloadUrl}
                    alt={`${work.expectedOutcome}. Zona aproximada: ${work.approximateZone}.`}
                  />
                  <span className="obra-caption">
                    <span className="chip chip--plain">
                      <span className="chip-key">{tradeKey(work.trade)}</span>
                      {tradeLabel(work.trade)}
                    </span>
                    <strong>{work.expectedOutcome}</strong>
                    <span>Zona aproximada: {work.approximateZone}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="stack" aria-labelledby="populares-titulo">
        <div className="cota">
          <p className="eyebrow">Calificados</p>
          <h2 id="populares-titulo">Los más populares</h2>
        </div>
        {loading ? (
          <p>Cargando calificados…</p>
        ) : providers.length === 0 && !error ? (
          <p>No hay calificados públicos todavía.</p>
        ) : (
          <ul className="calificados">
            {providers.map((provider) => (
              <li key={provider.id}>
                <article className="ficha">
                  <div className="ficha-inner">
                    <div
                      className={
                        provider.modality === "ORGANIZACION" ? "ficha-id ficha-id--org" : "ficha-id"
                      }
                      aria-hidden="true"
                    >
                      {initials(provider.name)}
                    </div>
                    <div className="ficha-title">
                      <h3 className="ficha-name">{provider.name}</h3>
                      <p className="ficha-meta">
                        {provider.verified ? "Verificado" : "Declarado"} · {provider.coverage.join(", ")}
                      </p>
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
                          {provider.rating.average.toFixed(1)}{" "}
                          <small>({provider.rating.count})</small>
                        </dd>
                      </div>
                      <div className="ficha-fact">
                        <dt>Obra concluida</dt>
                        <dd>{provider.concludedCount}</dd>
                      </div>
                    </dl>
                    <div className="ficha-actions">
                      <Link className="btn btn-ghost" to={`/calificados/${provider.id}`}>
                        Ver ficha
                      </Link>
                      <ContactCta provider={provider} />
                    </div>
                  </div>
                </article>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
