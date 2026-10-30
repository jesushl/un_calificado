import type { DiscoveryZone } from "../api/client"
import { MAX_DISTANCE_KM, MIN_DISTANCE_KM } from "../catalog"

type DiscoveryControlsProps = {
  zones: DiscoveryZone[]
  zone: string | null
  maxDistanceKm: number
  onZone: (zone: string) => void
  onDistance: (km: number) => void
  compact?: boolean
}

export function DiscoveryControls({
  zones,
  zone,
  maxDistanceKm,
  onZone,
  onDistance,
  compact = false,
}: DiscoveryControlsProps) {
  const span = MAX_DISTANCE_KM - MIN_DISTANCE_KM
  const reach = 32 + ((maxDistanceKm - MIN_DISTANCE_KM) / span) * 48

  return (
    <section className={compact ? "discovery discovery--compact plano" : "discovery plano"}>
      <div className="discovery-radar" aria-hidden="true">
        <span className="discovery-radar-ring discovery-radar-ring--max" />
        <span className="discovery-radar-ring" style={{ width: `${reach}%`, height: `${reach}%` }} />
        <span className="discovery-radar-core">{zone ? zone.slice(0, 3) : "zona"}</span>
      </div>
      <div className="stack">
        <p className="eyebrow">Tu zona</p>
        <h2 id="discovery-title">
          {zone ? `Hasta ${maxDistanceKm} km de ${zone}` : "Elige alcaldía y distancia"}
        </h2>
        <p>
          Así te mostramos calificados cerca, como en una app de citas: tú fijas el punto y hasta
          dónde te mueves. Usamos la alcaldía, no tu calle.
        </p>
        <fieldset className="field">
          <legend className="field-label">¿En qué alcaldía te mueves?</legend>
          <p className="field-hint">El domicilio exacto nunca se publica.</p>
          <div className="cluster" role="group" aria-label="Alcaldías">
            {zones.map((item) => (
              <button
                key={item.id}
                type="button"
                className="chip"
                aria-pressed={zone === item.id}
                onClick={() => onZone(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </fieldset>
        <label className="field">
          <span className="field-label">Distancia máxima</span>
          <p className="field-hint">{maxDistanceKm} km desde el centro de la alcaldía</p>
          <input
            className="range"
            type="range"
            min={MIN_DISTANCE_KM}
            max={MAX_DISTANCE_KM}
            step={1}
            value={maxDistanceKm}
            onChange={(event) => onDistance(Number(event.target.value))}
            aria-label="Distancia máxima"
            aria-valuemin={MIN_DISTANCE_KM}
            aria-valuemax={MAX_DISTANCE_KM}
            aria-valuenow={maxDistanceKm}
            aria-valuetext={`${maxDistanceKm} kilómetros`}
          />
          <span className="range-ends">
            <span>{MIN_DISTANCE_KM} km</span>
            <span>{MAX_DISTANCE_KM} km</span>
          </span>
        </label>
      </div>
    </section>
  )
}
