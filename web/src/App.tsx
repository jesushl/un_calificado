import type { ReactNode } from "react"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import { AuthProvider, useAuth } from "./auth/AuthContext"
import { Layout } from "./components/Layout"
import { ExplorePage } from "./pages/ExplorePage"
import { HomePage } from "./pages/HomePage"
import { LoginPage } from "./pages/LoginPage"
import { NewRequestPage } from "./pages/NewRequestPage"
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage"
import { ProviderPage } from "./pages/ProviderPage"
import { RegisterPage } from "./pages/RegisterPage"
import { RequestPage } from "./pages/RequestPage"
import { SettingsPage } from "./pages/SettingsPage"

function Guard({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <p className="container">Cargando sesión…</p>
  if (!user) return <Navigate to="/entrar" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/entrar" element={<LoginPage />} />
          <Route path="/entrar/oauth" element={<OAuthCallbackPage />} />
          <Route path="/registro" element={<RegisterPage />} />
          <Route element={<Layout />}>
            <Route path="/" element={<ExplorePage />} />
            <Route path="/calificados/:providerId" element={<ProviderPage />} />
            <Route
              path="/proyectos"
              element={
                <Guard>
                  <HomePage />
                </Guard>
              }
            />
            <Route
              path="/cuenta"
              element={
                <Guard>
                  <SettingsPage />
                </Guard>
              }
            />
            <Route
              path="/nuevo"
              element={
                <Guard>
                  <NewRequestPage />
                </Guard>
              }
            />
            <Route
              path="/proyectos/:requestId"
              element={
                <Guard>
                  <RequestPage />
                </Guard>
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
