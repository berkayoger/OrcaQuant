import { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { ToastCenter } from '@/components/ToastCenter';

interface AppLayoutProps {
  children: ReactNode;
}

const navLinkClass = ({ isActive }: { isActive: boolean }): string =>
  [
    'rounded-xl px-4 py-2 text-sm font-semibold transition',
    isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:text-white',
  ].join(' ');

export const AppLayout = ({ children }: AppLayoutProps): JSX.Element => {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = (): void => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <ToastCenter />
      <header className="border-b border-slate-800/60 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <NavLink to="/" className="text-lg font-bold text-white">
            OrcaQuant
          </NavLink>
          <nav className="hidden items-center gap-3 md:flex">
            <NavLink to="/" className={navLinkClass}>
              Anasayfa
            </NavLink>
            <NavLink to="/dashboard" className={navLinkClass}>
              Dashboard
            </NavLink>
            {user?.role === 'admin' && (
              <NavLink to="/admin" className={navLinkClass}>
                Admin
              </NavLink>
            )}
          </nav>
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <span className="hidden text-sm text-slate-300 md:inline">{user?.name}</span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-accent/60 hover:text-white"
                >
                  Çıkış
                </button>
              </>
            ) : (
              <>
                <NavLink
                  to="/login"
                  className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-accent/60 hover:text-white"
                >
                  Giriş Yap
                </NavLink>
                <NavLink
                  to="/register"
                  className="rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-cyan-400"
                >
                  Kayıt Ol
                </NavLink>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-10">{children}</main>
      <footer className="border-t border-slate-800/60 bg-slate-950/80 py-6 text-center text-sm text-slate-500">
        © {new Date().getFullYear()} OrcaQuant. Tüm hakları saklıdır.
      </footer>
    </div>
  );
};
