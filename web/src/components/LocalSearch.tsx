import { useEffect, useState, type FormEvent } from "react"

type LocalSearchProps = {
  value: string
  onSearch: (query: string) => void
}

export function LocalSearch({ value, onSearch }: LocalSearchProps) {
  const [draft, setDraft] = useState(value)

  useEffect(() => {
    setDraft(value)
  }, [value])

  useEffect(() => {
    const handle = window.setTimeout(() => {
      if (draft.trim() === value.trim()) return
      onSearch(draft.trim())
    }, 320)
    return () => window.clearTimeout(handle)
    // Solo reaccionamos al texto; onSearch viene del padre y cambia por render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft, value])

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    onSearch(draft.trim())
  }

  return (
    <form className="stack" onSubmit={onSubmit} role="search" data-testid="local-search">
      <label className="field">
        <span className="field-label">Buscar en el índice</span>
        <input
          className="input"
          type="search"
          name="q"
          value={draft}
          placeholder="Nombre, oficio o tipo de trabajo — ej. herrería, reja, Doña Lucha"
          onChange={(event) => setDraft(event.target.value)}
          data-testid="local-search-input"
          autoComplete="off"
        />
        <span className="field-hint">
          Busca por calificado, oficio (plomería, albañilería…) o lo que necesitas que quede listo.
        </span>
      </label>
      <div className="cluster">
        <button className="btn btn-primary" type="submit">
          Buscar
        </button>
        {value ? (
          <button
            className="btn btn-ghost"
            type="button"
            onClick={() => {
              setDraft("")
              onSearch("")
            }}
          >
            Limpiar
          </button>
        ) : null}
      </div>
    </form>
  )
}
