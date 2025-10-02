import { useEffect, useMemo } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useLivePrices } from '@/hooks/useLivePrices';
import { usePredictionStore } from '@/store/predictionStore';
import { LoadingSpinner } from './LoadingSpinner';

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return `${date.getHours().toString().padStart(2, '0')}:${date
    .getMinutes()
    .toString()
    .padStart(2, '0')}`;
};

export const PredictionDisplay = (): JSX.Element => {
  const predictions = usePredictionStore((state) => state.predictions);
  const latestPrice = usePredictionStore((state) => state.latestPrice);
  const fetchPredictions = usePredictionStore((state) => state.fetchPredictions);
  const isLoading = usePredictionStore((state) => state.isLoading);
  const error = usePredictionStore((state) => state.error);

  useEffect(() => {
    void fetchPredictions();
  }, [fetchPredictions]);

  useLivePrices(true);

  const chartData = useMemo(
    () =>
      predictions
        .slice(0)
        .reverse()
        .map((prediction) => ({
          time: formatTimestamp(prediction.createdAt),
          price: prediction.predictedPrice,
          confidence: prediction.confidence,
        })),
    [predictions],
  );

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/50 bg-red-500/10 p-6 text-red-200">
        <h3 className="text-lg font-semibold">Tahminler yüklenemedi</h3>
        <p className="mt-2 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Gerçek Zamanlı Tahminler</h2>
          <span className="text-xs uppercase tracking-widest text-slate-400">AI MODELLERI</span>
        </div>
        <div className="mt-6 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="time" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: '0.75rem' }}
                labelStyle={{ color: '#cbd5f5' }}
              />
              <Area type="monotone" dataKey="price" stroke="#60a5fa" fill="url(#colorPrice)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="space-y-4">
        {predictions.slice(0, 6).map((prediction) => {
          const livePrice = latestPrice[prediction.asset];
          const hasLivePrice = typeof livePrice === 'number';
          const delta = hasLivePrice
            ? ((livePrice - prediction.predictedPrice) / prediction.predictedPrice) * 100
            : 0;
          const deltaColor = delta >= 0 ? 'text-emerald-400' : 'text-rose-400';

          return (
            <div
              key={prediction.id}
              className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 transition hover:border-accent/50"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">{prediction.asset}</h3>
                  <p className="text-sm text-slate-400">Güven: %{Math.round(prediction.confidence * 100)}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">${prediction.predictedPrice.toFixed(2)}</p>
                  {hasLivePrice && (
                    <p className={`text-sm ${deltaColor}`}>
                      Canlı: ${livePrice.toFixed(2)} ({delta >= 0 ? '+' : ''}{delta.toFixed(2)}%)
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        {predictions.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-700 p-6 text-center text-slate-400">
            Henüz tahmin yok. Modellerimiz canlı verileri dinliyor.
          </div>
        )}
      </div>
    </div>
  );
};
