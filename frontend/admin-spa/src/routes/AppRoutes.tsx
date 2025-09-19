import { lazy } from 'react'
import { Navigate, NavLink as RRNavLink, Outlet, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import LoginPage from '../pages/LoginPage'

const DashboardPage = lazy(() => import('../pages/DashboardPage'))
const UsersPage = lazy(() => import('../pages/UsersPage'))

function ProtectedRoute() {
  const isSession = useAuthStore((state) => state.isSession)
  return isSession ? <Outlet /> : <Navigate to="/login" replace />
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AdminLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="users" element={<UsersPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function AdminLayout() {
  return (
    <div className="min-h-screen grid grid-cols-[240px_1fr]">
      <aside className="bg-neutral-950 border-r border-neutral-800 p-4 space-y-6">
        <div>
          <h1 className="text-xl font-semibold">YTD Admin</h1>
          <p className="text-xs text-neutral-500">Kontrol paneli</p>
        </div>
        <nav className="space-y-2">
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/users">Kullanıcılar</NavLink>
        </nav>
      </aside>
      <main className="bg-neutral-900 min-h-screen">
        <Outlet />
      </main>
    </div>
  )
}

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <RRNavLink
      to={to}
      end
      className={({ isActive }) =>
        `block px-3 py-2 rounded-md text-sm font-medium ${
          isActive ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-white hover:bg-neutral-900'
        }`
      }
    >
      {children}
    </RRNavLink>
  )
}
