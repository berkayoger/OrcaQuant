export default function Subscription() {
  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      <h1 style={{ fontSize: '32px', fontWeight: '800' }}>Abonelik Planları</h1>
      
      <div style={{
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '24px'
      }}>
        <h2 style={{ marginBottom: '16px' }}>Premium Özellikler</h2>
        <p style={{ color: 'var(--muted)' }}>
          Abonelik yönetimi burada yer alacak.
        </p>
      </div>
    </div>
  );
}
