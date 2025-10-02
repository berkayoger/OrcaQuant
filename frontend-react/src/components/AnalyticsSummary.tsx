import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { AnalyticsMetric, AnalyticsPoint } from '@/store/adminAnalyticsStore';

interface AnalyticsSummaryProps {
  metrics: AnalyticsMetric[];
  revenueSeries: AnalyticsPoint[];
  retentionSeries: AnalyticsPoint[];
}

export const AnalyticsSummary = ({ metrics, revenueSeries, retentionSeries }: AnalyticsSummaryProps): JSX.Element => (
  <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
    <div className="xl:col-span-1 space-y-4">
      {metrics.map((metric) => {
        const isPositive = metric.change >= 0;
        const changeColor = isPositive ? 'text-emerald-400' : 'text-rose-400';
        const changePrefix = isPositive ? '+' : '';
        return (
          <div key={metric.label} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <p className="text-sm uppercase tracking-widest text-slate-400">{metric.label}</p>
            <p className="mt-2 text-3xl font-bold text-white">{metric.value.toLocaleString('tr-TR')}</p>
            <p className={`text-sm ${changeColor}`}>{changePrefix}{metric.change.toFixed(2)}%</p>
          </div>
        );
      })}
    </div>
    <div className="xl:col-span-2 grid grid-cols-1 gap-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Aylık Gelir</h3>
          <span className="text-xs uppercase tracking-widest text-slate-400">USD</span>
        </div>
        <div className="mt-4 h-60">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={revenueSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="timestamp" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: '0.75rem' }}
                labelStyle={{ color: '#cbd5f5' }}
              />
              <Line type="monotone" dataKey="value" stroke="#22d3ee" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Kullanıcı Tutma Oranı</h3>
          <span className="text-xs uppercase tracking-widest text-slate-400">%</span>
        </div>
        <div className="mt-4 h-60">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={retentionSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="timestamp" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: '0.75rem' }}
                labelStyle={{ color: '#cbd5f5' }}
              />
              <Line type="monotone" dataKey="value" stroke="#a855f7" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  </div>
);
