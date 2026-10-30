import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import { api, ApiError, getToken, setToken, type User } from "../api/client"
import { dataRole, readGuestDiscovery, userDiscovery } from "../catalog"

type AuthState = {
  user: User | null
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (payload: {
    email: string
    password: string
    role: "CLIENTE" | "PROVEEDOR"
  }) => Promise<void>
  acceptSession: (token: string, user: User) => void
  updateProfile: (payload: {
    name?: string
    searchZone?: string
    maxDistanceKm?: number
  }) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(Boolean(getToken()))
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!getToken()) return
    api
      .me()
      .then(setUser)
      .catch(() => {
        setToken(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    document.documentElement.lang = "es-MX"
    document.documentElement.dataset.role = dataRole(user?.role)
  }, [user])

  const adoptGuestDiscovery = useCallback(async (nextUser: User) => {
    if (userDiscovery(nextUser).zone) {
      setUser(nextUser)
      return
    }
    const guest = readGuestDiscovery()
    if (!guest.zone) {
      setUser(nextUser)
      return
    }
    try {
      const saved = await api.updateMe({
        searchZone: guest.zone,
        maxDistanceKm: guest.maxDistanceKm,
      })
      setUser(saved)
    } catch {
      setUser(nextUser)
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setError(null)
    try {
      const response = await api.login(email, password)
      setToken(response.access_token)
      await adoptGuestDiscovery(response.user)
    } catch (caught) {
      setToken(null)
      const message =
        caught instanceof ApiError
          ? caught.status === 401
            ? "Correo o contraseña incorrectos. Revísalos e intenta de nuevo."
            : caught.message
          : "No pudimos conectar. Revisa tu internet y vuelve a intentar."
      setError(message)
      throw caught
    }
  }, [adoptGuestDiscovery])

  const register = useCallback(
    async (payload: { email: string; password: string; role: "CLIENTE" | "PROVEEDOR" }) => {
      setError(null)
      await api.register({
        ...payload,
        privacy_consent_version: "2026-01",
        adult_declaration: true,
      })
      await login(payload.email, payload.password)
    },
    [adoptGuestDiscovery, login],
  )

  const acceptSession = useCallback(
    (token: string, nextUser: User) => {
      setToken(token)
      setError(null)
      void adoptGuestDiscovery(nextUser)
    },
    [adoptGuestDiscovery],
  )

  const updateProfile = useCallback(
    async (payload: { name?: string; searchZone?: string; maxDistanceKm?: number }) => {
      const next = await api.updateMe(payload)
      setUser(next)
    },
    [],
  )

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      /* el token local se borra de todos modos */
    }
    setToken(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, error, login, register, acceptSession, updateProfile, logout }),
    [user, loading, error, login, register, acceptSession, updateProfile, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth requiere AuthProvider")
  return context
}
