export default function Register() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'grid',
      placeItems: 'center'
    }}>
      <div style={{
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '32px',
        maxWidth: '400px',
        width: '100%'
      }}>
        <h1 style={{ marginBottom: '24px', textAlign: 'center' }}>Kayıt Ol</h1>
        <p style={{ color: 'var(--muted)', textAlign: 'center' }}>
          Kayıt formu burada geliştirilecek.
        </p>
      </div>
    </div>
  );
}
