import { useEffect, useState, type FormEvent } from "react"
import { Link, Navigate } from "react-router-dom"

import { api, ApiError, type DiscoveryZone } from "../api/client"
import { useAuth } from "../auth/AuthContext"
import { accountLabel, DEFAULT_DISTANCE_KM, readGuestDiscovery, userDiscovery } from "../catalog"
import { DiscoveryControls } from "../components/DiscoveryControls"

export function SettingsPage() {
  const { user, loading, updateProfile } = useAuth()
  const saved = userDiscovery(user)
  const guest = readGuestDiscovery()
  const [zones, setZones] = useState<DiscoveryZone[]>([])
  const [zone, setZone] = useState(saved.zone || guest.zone)
  const [maxDistanceKm, setMaxDistanceKm] = useState(saved.zone ? saved.maxDistanceKm : guest.maxDistanceKm)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    api
      .discoveryZones()
      .then((payload) => setZones(payload.items))
      .catch((caught: Error) => setError(caught.message))
  }, [])

  useEffect(() => {
    if (!user) return
    const next = userDiscovery(user)
    if (next.zone) {
      setZone(next.zone)
      setMaxDistanceKm(next.maxDistanceKm)
    }
  }, [user])

  if (loading) return <p>Cargando sesión…</p>
  if (!user) return <Navigate to="/entrar?siguiente=/cuenta" replace />

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!zone) {
      setError("Elige una alcaldía para ver calificados cerca.")
      return
    }
    setPending(true)
    setError(null)
    setNotice(null)
    try {
      await updateProfile({ searchZone: zone, maxDistanceKm })
      setNotice("Cambios guardados.")
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "No pudimos conectar. Revisa tu internet y vuelve a intentar.",
      )
    } finally {
      setPending(false)
    }
  }

  return (
    <section className="stack stack--lg">
      <div className="cota">
        <p className="eyebrow">Cuenta</p>
        <h1>A quién ves cerca</h1>
      </div>
      <p data-testid="account-summary">
        Sesión de <strong>{accountLabel(user)}</strong>
        {user.email ? ` · ${user.email}` : ""}.
      </p>
      <p>
        El índice solo muestra calificados dentro de esta distancia. Puedes cambiarla cuando
        quieras. Tu calle y número se quedan contigo.
      </p>
      {error ? (
        <p className="alert alert--danger" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? (
        <p className="alert" role="status">
          {notice}
        </p>
      ) : null}
      <form className="stack stack--lg" onSubmit={(event) => void onSubmit(event)}>
        <DiscoveryControls
          zones={zones}
          zone={zone}
          maxDistanceKm={maxDistanceKm || DEFAULT_DISTANCE_KM}
          onZone={setZone}
          onDistance={setMaxDistanceKm}
        />
        <div className="cluster">
          <button className="btn btn-primary" type="submit" disabled={pending}>
            {pending ? "Guardando cambios…" : "Guardar zona"}
          </button>
          <Link className="btn btn-ghost" to="/">
            Ver calificados de tu zona
          </Link>
        </div>
      </form>
    </section>
  )
}
