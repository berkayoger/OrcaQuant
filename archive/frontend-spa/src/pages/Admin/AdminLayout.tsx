import { Routes, Route, NavLink } from 'react-router-dom';
import UserManagement from './UserManagement';
import AdminAnalytics from './AdminAnalytics';

export default function AdminLayout() {
  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '800' }}>Admin Panel</h1>
        <nav style={{ display: 'flex', gap: '16px' }}>
          <NavLink 
            to="/admin/users"
            style={({ isActive }) => ({
              padding: '8px 16px',
              borderRadius: '6px',
              background: isActive ? 'var(--accent)' : 'var(--bg)',
              color: isActive ? 'var(--bg)' : 'var(--text)',
              border: '1px solid var(--border)'
            })}
          >
            Kullanıcılar
          </NavLink>
          <NavLink 
            to="/admin/analytics"
            style={({ isActive }) => ({
              padding: '8px 16px',
              borderRadius: '6px',
              background: isActive ? 'var(--accent)' : 'var(--bg)',
              color: isActive ? 'var(--bg)' : 'var(--text)',
              border: '1px solid var(--border)'
            })}
          >
            Analytics
          </NavLink>
        </nav>
      </div>

      <Routes>
        <Route path="users" element={<UserManagement />} />
        <Route path="analytics" element={<AdminAnalytics />} />
        <Route index element={<AdminAnalytics />} />
      </Routes>
    </div>
  );
}
