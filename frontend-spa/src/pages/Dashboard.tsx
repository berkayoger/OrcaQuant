import { useEffect, useState } from 'react';
import ChartCard from '../components/ChartCard';
import { wsService } from '../services/websocket';
import { cryptoAPI } from '../services/api';

interface PriceData {
  time: string;
  price: number;
}

interface MarketStats {
  symbol: string;
  price: number;
  change24h: number;
  volume: number;
}

export default function Dashboard() {
  const [priceData, setPriceData] = useState<PriceData[]>([]);
  const [marketStats, setMarketStats] = useState<MarketStats | null>(null);
  const [portfolioValue, setPortfolioValue] = useState<number>(0);

  useEffect(() => {
    // Initialize WebSocket connection
    const socket = wsService.connect();
    
    socket.on('price', (data) => {
      const newPoint = {
        time: new Date(data.ts).toLocaleTimeString('tr-TR', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }),
        price: data.price
      };
      
      setPriceData(prev => [...prev.slice(-50), newPoint]);
      
      setMarketStats(prev => ({
        symbol: data.symbol,
        price: data.price,
        change24h: prev ? ((data.price - prev.price) / prev.price) * 100 : 0,
        volume: data.volume || 0
      }));
    });

    // Fetch initial data
    fetchInitialData();

    return () => {
      wsService.disconnect();
    };
  }, []);

  const fetchInitialData = async () => {
    try {
      const [marketResponse, portfolioResponse] = await Promise.all([
        cryptoAPI.getMarketData(),
        cryptoAPI.getPortfolio()
      ]);
      
      setMarketStats({
        symbol: marketResponse.data.symbol,
        price: marketResponse.data.price,
        change24h: 0,
        volume: 0
      });
      
      setPortfolioValue(portfolioResponse.data.total_value_usd);
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      {/* Stats Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '16px'
      }}>
        <div style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <div style={{ color: 'var(--muted)', fontSize: '14px', marginBottom: '8px' }}>
            BTC/USDT Fiyatı
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', marginBottom: '4px' }}>
            {marketStats ? formatCurrency(marketStats.price) : '---'}
          </div>
          <div style={{
            color: marketStats && marketStats.change24h >= 0 ? 'var(--success)' : 'var(--error)',
            fontSize: '14px'
          }}>
            {marketStats ? formatPercentage(marketStats.change24h) : '0.00%'}
          </div>
        </div>

        <div style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <div style={{ color: 'var(--muted)', fontSize: '14px', marginBottom: '8px' }}>
            Portföy Değeri
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', marginBottom: '4px' }}>
            {formatCurrency(portfolioValue)}
          </div>
          <div style={{ color: 'var(--success)', fontSize: '14px' }}>
            +2.34% (24s)
          </div>
        </div>

        <div style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <div style={{ color: 'var(--muted)', fontSize: '14px', marginBottom: '8px' }}>
            Aktif Pozisyonlar
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', marginBottom: '4px' }}>
            12
          </div>
          <div style={{ color: 'var(--muted)', fontSize: '14px' }}>
            8 Karlı, 4 Zararlı
          </div>
        </div>
      </div>

      {/* Price Chart */}
      {priceData.length > 0 && (
        <ChartCard 
          title="BTC/USDT Canlı Fiyat Grafiği"
          data={priceData}
          height={400}
        />
      )}

      {/* Quick Actions */}
      <div style={{
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '20px'
      }}>
        <h3 style={{ marginBottom: '16px' }}>Hızlı İşlemler</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px'
        }}>
          <button style={{
            padding: '12px 16px',
            background: 'var(--accent)',
            color: 'var(--bg)',
            borderRadius: '8px',
            fontWeight: '600'
          }}>
            Yeni Analiz
          </button>
          <button style={{
            padding: '12px 16px',
            background: 'var(--bg)',
            color: 'var(--text)',
            border: '1px solid var(--border)',
            borderRadius: '8px'
          }}>
            Uyarı Oluştur
          </button>
          <button style={{
            padding: '12px 16px',
            background: 'var(--bg)',
            color: 'var(--text)',
            border: '1px solid var(--border)',
            borderRadius: '8px'
          }}>
            Rapor İndir
          </button>
        </div>
      </div>
    </div>
  );
}
