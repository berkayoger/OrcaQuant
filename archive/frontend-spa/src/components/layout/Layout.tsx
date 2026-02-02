import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '260px 1fr',
      height: '100vh',
      background: 'var(--bg)'
    }}>
      <Sidebar />
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0
      }}>
        <Header />
        <main style={{
          flex: 1,
          padding: '24px',
          overflow: 'auto'
        }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
