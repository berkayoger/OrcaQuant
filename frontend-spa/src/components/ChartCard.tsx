import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

interface DataPoint {
  time: string;
  price: number;
}

interface ChartCardProps {
  title: string;
  data: DataPoint[];
  height?: number;
}

export default function ChartCard({ title, data, height = 300 }: ChartCardProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(price);
  };

  return (
    <div style={{
      background: 'var(--card)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: '20px'
    }}>
      <h3 style={{ 
        color: 'var(--muted)',
        fontSize: '16px',
        fontWeight: '600',
        marginBottom: '16px'
      }}>
        {title}
      </h3>
      
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <XAxis 
              dataKey="time" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'var(--muted)', fontSize: 12 }}
            />
            <YAxis 
              hide 
              domain={['dataMin - 100', 'dataMax + 100']}
            />
            <Tooltip 
              contentStyle={{
                background: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                color: 'var(--text)'
              }}
              formatter={(value: number) => [formatPrice(value), 'Fiyat']}
              labelStyle={{ color: 'var(--muted)' }}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="var(--accent)" 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: 'var(--accent)' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
