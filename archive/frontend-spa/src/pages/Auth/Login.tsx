import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const login = useAuthStore(state => state.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Giriş başarısız');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'grid',
      placeItems: 'center',
      background: 'var(--bg)',
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '32px'
      }}>
        {/* Brand */}
        <div style={{
          textAlign: 'center',
          marginBottom: '32px'
        }}>
          <h1 style={{
            fontSize: '32px',
            fontWeight: '800',
            color: 'var(--accent)',
            marginBottom: '8px'
          }}>
            OrcaQuant
          </h1>
          <p style={{ color: 'var(--muted)' }}>
            Hesabınıza giriş yapın
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              fontWeight: '500'
            }}>
              E-posta
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ornek@email.com"
              required
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              fontWeight: '500'
            }}>
              Şifre
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={{ width: '100%' }}
            />
          </div>

          {error && (
            <div style={{
              color: 'var(--error)',
              fontSize: '14px',
              marginBottom: '16px',
              padding: '8px 12px',
              background: 'rgba(239, 68, 68, 0.1)',
              borderRadius: '6px'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px',
              background: 'var(--accent)',
              color: 'var(--bg)',
              fontWeight: '600',
              borderRadius: '8px',
              fontSize: '16px',
              opacity: loading ? 0.7 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
          </button>
        </form>

        {/* Register Link */}
        <div style={{
          textAlign: 'center',
          marginTop: '24px',
          padding: '16px 0',
          borderTop: '1px solid var(--border)'
        }}>
          <span style={{ color: 'var(--muted)' }}>
            Hesabınız yok mu?{' '}
          </span>
          <Link 
            to="/register"
            style={{ color: 'var(--accent)', fontWeight: '500' }}
          >
            Kayıt olun
          </Link>
        </div>
      </div>
    </div>
  );
}
