export default function Analytics() {
  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      <h1 style={{ fontSize: '32px', fontWeight: '800' }}>Analitik</h1>
      
      <div style={{
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '24px'
      }}>
        <h2 style={{ marginBottom: '16px' }}>AI Tahminleri</h2>
        <p style={{ color: 'var(--muted)' }}>
          AI analiz motoru entegrasyonu burada yer alacak.
        </p>
      </div>
    </div>
  );
}
