import { Link, NavLink, Outlet } from "react-router-dom"

import { Wordmark } from "../brand/Mark"
import { dataRole } from "../catalog"
import { useAuth } from "../auth/AuthContext"

const LINKS = {
  CLIENTE: [
    { to: "/", label: "Índice" },
    { to: "/proyectos", label: "Proyectos" },
    { to: "/nuevo", label: "Crear proyecto" },
    { to: "/cuenta", label: "Cuenta" },
  ],
  PROVEEDOR: [
    { to: "/", label: "Índice" },
    { to: "/proyectos", label: "Solicitudes" },
    { to: "/cuenta", label: "Cuenta" },
  ],
  ADMINISTRADOR: [
    { to: "/", label: "Índice" },
    { to: "/proyectos", label: "Operación" },
    { to: "/cuenta", label: "Cuenta" },
  ],
}

const PUBLIC_LINKS = [
  { to: "/", label: "Índice" },
  { to: "/entrar", label: "Entrar" },
  { to: "/registro", label: "Crear cuenta" },
]

export function Layout() {
  const { user, logout } = useAuth()
  const role = user?.role ?? "CLIENTE"
  const links = user ? LINKS[role] : PUBLIC_LINKS

  return (
    <div data-role={dataRole(user?.role)}>
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <header className="nav">
        <div className="nav-inner">
          <Wordmark />
          <nav aria-label="Principal">
            <ul className="nav-links">
              {links.map((link) => (
                <li key={link.to}>
                  <NavLink
                    to={link.to}
                    className={({ isActive }) => (isActive ? "nav-link is-active" : "nav-link")}
                    end={link.to === "/"}
                  >
                    {link.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="cluster" style={{ marginLeft: "auto" }}>
            {user ? (
              <>
                <span className="role-tag" data-role={dataRole(role)}>
                  {role === "PROVEEDOR"
                    ? "Proveedor"
                    : role === "ADMINISTRADOR"
                      ? "Administrador"
                      : "Cliente"}
                </span>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => void logout()}>
                  Cerrar sesión
                </button>
              </>
            ) : (
              <Link className="btn btn-primary btn-sm" to="/entrar">
                Entrar
              </Link>
            )}
          </div>
        </div>
      </header>
      <main id="contenido" className="container" style={{ paddingBlock: "var(--space-7)" }}>
        <Outlet />
      </main>
      <footer className="container" style={{ paddingBlock: "var(--space-8)", color: "var(--color-ink-soft)" }}>
        <p>UnCalificado no cobra ni procesa pagos. El pago lo acuerdas directamente con el proveedor.</p>
        <p>Tu domicilio exacto nunca se publica.</p>
      </footer>
    </div>
  )
}
