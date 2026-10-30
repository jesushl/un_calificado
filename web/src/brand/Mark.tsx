import type { CSSProperties } from "react"
import { Link } from "react-router-dom"

export function Mark({ className = "wordmark-mark" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden="true">
      <path
        d="M5 16.5 12.5 24 27.5 7.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="5"
        strokeLinejoin="miter"
        strokeMiterlimit={4}
      />
      <path
        d="M17.71 21.98L20.23 24.27M20.07 19.39L21.70 20.87M22.42 16.80L24.94 19.09M24.78 14.21L26.40 15.69M27.13 11.62L29.65 13.91"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  )
}

export function Wordmark({
  to = "/",
  size,
}: {
  to?: string
  size?: string
}) {
  const style = size ? ({ ["--wm-size"]: size } as CSSProperties) : undefined
  return (
    <Link
      className="wordmark nav-brand"
      to={to}
      aria-label="UnCalificado, inicio"
      style={style}
    >
      <Mark />
      <span>
        <span className="wordmark-un">Un</span>
        <span className="wordmark-cal">Calificado</span>
      </span>
    </Link>
  )
}
