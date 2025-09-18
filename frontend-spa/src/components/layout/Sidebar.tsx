import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Portföy', href: '/portfolio', icon: '💰' },
  { name: 'Analitik', href: '/analytics', icon: '📈' },
  { name: 'Abonelik', href: '/subscription', icon: '💳' },
  { name: 'Admin', href: '/admin', icon: '⚙️' }
];

export default function Sidebar() {
  const navigate = useNavigate();
  const logout = useAuthStore(state => state.logout);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{
      background: 'var(--card)',
      borderRight: '1px solid var(--border)',
      padding: '24px 16px',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Brand */}
      <div style={{
        fontSize: '24px',
        fontWeight: '800',
        color: 'var(--accent)',
        marginBottom: '32px',
        textAlign: 'center'
      }}>
        OrcaQuant
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1 }}>
        <ul style={{ listStyle: 'none' }}>
          {navigation.map((item) => (
            <li key={item.name} style={{ marginBottom: '8px' }}>
              <NavLink
                to={item.href}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '10px',
                  color: isActive ? 'var(--text)' : 'var(--muted)',
                  background: isActive ? 'var(--bg)' : 'transparent',
                  border: isActive ? '1px solid var(--border)' : '1px solid transparent',
                  transition: 'all 0.2s ease'
                })}
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        style={{
          width: '100%',
          padding: '12px',
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: '10px',
          color: 'var(--text)',
          transition: 'all 0.2s ease'
        }}
      >
        Çıkış Yap
      </button>
    </div>
  );
}
