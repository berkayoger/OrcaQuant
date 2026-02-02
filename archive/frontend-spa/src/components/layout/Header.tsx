import { useAuthStore } from '../../store/auth';

export default function Header() {
  const user = useAuthStore(state => state.user);

  return (
    <header style={{
      height: '64px',
      borderBottom: '1px solid var(--border)',
      background: 'var(--card)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: '600' }}>
          {getPageTitle()}
        </h1>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        color: 'var(--muted)'
      }}>
        <span>👤</span>
        <span>{user?.email || 'Kullanıcı'}</span>
      </div>
    </header>
  );
}

function getPageTitle() {
  const path = window.location.pathname;
  const titles: Record<string, string> = {
    '/': 'Dashboard',
    '/portfolio': 'Portföy',
    '/analytics': 'Analitik',
    '/subscription': 'Abonelik',
    '/admin': 'Admin Panel'
  };
  
  return titles[path] || 'OrcaQuant';
}
