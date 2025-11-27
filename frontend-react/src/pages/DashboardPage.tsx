import { useMemo } from 'react';
import { PredictionDisplay } from '@/components/PredictionDisplay';
import { AnalyticsSummary } from '@/components/AnalyticsSummary';
import { PlanUsagePanel } from '@/components/PlanUsagePanel';
import { usePlanLimits } from '@/hooks/usePlanLimits';
import { usePredictionStore } from '@/store/predictionStore';

export const DashboardPage = (): JSX.Element => {
  const predictions = usePredictionStore((state) => state.predictions);
  const { data: limits, loading: limitsLoading } = usePlanLimits();

  const metrics = useMemo(() => {
    const avgConfidence = predictions.length
      ? predictions.reduce((total, prediction) => total + prediction.confidence, 0) / predictions.length
      : 0;
    const trackedAssets = new Set(predictions.map((prediction) => prediction.asset)).size;

    return [
      {
        label: 'Aktif Tahminler',
        value: predictions.length || 12,
        change: 8.4,
      },
      {
        label: 'Ortalama Güven',
        value: Math.round(avgConfidence * 100) || 85,
        change: 4.1,
      },
      {
        label: 'Takip Edilen Varlık',
        value: trackedAssets || 6,
        change: 2.7,
      },
    ];
  }, [predictions]);

  const revenueSeries = useMemo(
    () =>
      predictions.length
        ? predictions
            .slice(0, 12)
            .reverse()
            .map((prediction) => ({ timestamp: prediction.createdAt, value: prediction.predictedPrice }))
        : Array.from({ length: 8 }, (_, index) => ({ timestamp: `Hafta ${index + 1}`, value: 5000 + index * 750 })),
    [predictions],
  );

  const retentionSeries = useMemo(
    () =>
      predictions.length
        ? predictions
            .slice(0, 12)
            .reverse()
            .map((prediction) => ({ timestamp: prediction.createdAt, value: Math.round(prediction.confidence * 100) }))
        : Array.from({ length: 8 }, (_, index) => ({ timestamp: `Hafta ${index + 1}`, value: 70 + index * 2 })),
    [predictions],
  );

  return (
    <div className="space-y-12">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Yatırım Panosu</h1>
            <p className="mt-2 max-w-xl text-sm text-slate-400">
              Gerçek zamanlı tahminler, canlı fiyatlar ve AI modellerimizden gelen içgörüler ile
              portföyünüzü güçlendirin.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-700 bg-slate-950 px-6 py-4 text-right">
            <p className="text-xs uppercase tracking-widest text-slate-400">Toplam Beklenen Getiri</p>
            <p className="text-2xl font-semibold text-emerald-400">+%12.6</p>
          </div>
        </div>
        <div className="mt-6">
          <PredictionDisplay />
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-white">Plan ve Kullanım</h2>
          {limitsLoading && <span className="text-xs text-slate-400">Limit bilgisi yükleniyor...</span>}
        </div>
        {limits && <PlanUsagePanel data={limits} />}
      </section>

      <section className="space-y-6">
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-semibold text-white">Performans ve Trendler</h2>
          <p className="text-sm text-slate-400">
            Piyasa davranışını izleyin, riskinizi yönetin ve getirilerinizi büyütmek için fırsatları
            değerlendirin.
          </p>
        </div>
        <AnalyticsSummary metrics={metrics} revenueSeries={revenueSeries} retentionSeries={retentionSeries} />
      </section>
    </div>
  );
};
