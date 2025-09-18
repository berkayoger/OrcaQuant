import { useEffect, useState } from 'react';
import { cryptoAPI } from '../services/api';

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const response = await cryptoAPI.getPortfolio();
      setPortfolio(response.data);
    } catch (error) {
      console.error('Portfolio fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="spinner" />;
  }

  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      <h1 style={{ fontSize: '32px', fontWeight: '800' }}>Portföy</h1>
      
      {portfolio && (
        <>
          <div style={{
            background: 'var(--card)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            padding: '24px'
          }}>
            <h2 style={{ marginBottom: '16px' }}>Toplam Değer</h2>
            <div style={{ fontSize: '36px', fontWeight: '800', color: 'var(--accent)' }}>
              ${portfolio.total_value_usd.toLocaleString()}
            </div>
          </div>

          <div style={{
            background: 'var(--card)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            padding: '24px'
          }}>
            <h2 style={{ marginBottom: '16px' }}>Pozisyonlar</h2>
            <div style={{ display: 'grid', gap: '12px' }}>
              {portfolio.positions.map((position: any, index: number) => (
                <div key={index} style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr auto auto',
                  alignItems: 'center',
                  gap: '16px',
                  padding: '16px',
                  background: 'var(--bg)',
                  borderRadius: '8px'
                }}>
                  <div>
                    <div style={{ fontWeight: '600' }}>{position.symbol}</div>
                    <div style={{ color: 'var(--muted)', fontSize: '14px' }}>
                      {position.amount} adet
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div>${position.current_price.toFixed(2)}</div>
                    <div style={{ color: 'var(--muted)', fontSize: '14px' }}>
                      Ort: ${position.avg_price.toFixed(2)}
                    </div>
                  </div>
                  <div style={{
                    color: position.pnl_pct >= 0 ? 'var(--success)' : 'var(--error)',
                    fontWeight: '600'
                  }}>
                    {position.pnl_pct >= 0 ? '+' : ''}{position.pnl_pct.toFixed(2)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
