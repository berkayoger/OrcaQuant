import { useEffect } from 'react';
import { AnalyticsSummary } from '@/components/AnalyticsSummary';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useAdminAnalyticsStore } from '@/store/adminAnalyticsStore';

export const AdminDashboard = (): JSX.Element => {
  const metrics = useAdminAnalyticsStore((state) => state.metrics);
  const revenueSeries = useAdminAnalyticsStore((state) => state.revenueSeries);
  const retentionSeries = useAdminAnalyticsStore((state) => state.retentionSeries);
  const fetchAnalytics = useAdminAnalyticsStore((state) => state.fetchAnalytics);
  const isLoading = useAdminAnalyticsStore((state) => state.isLoading);
  const error = useAdminAnalyticsStore((state) => state.error);

  useEffect(() => {
    void fetchAnalytics();
  }, [fetchAnalytics]);

  return (
    <div className="space-y-10">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Yönetici Analizleri</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Kullanıcı davranışını, abonelik gelirini ve platform performansını yakından izleyin.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-700 bg-slate-950 px-6 py-4 text-right">
            <p className="text-xs uppercase tracking-widest text-slate-400">Aylık MRR</p>
            <p className="text-2xl font-semibold text-accent">$128,450</p>
          </div>
        </div>
        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="mt-6 rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-rose-200">{error}</div>
        ) : (
          <div className="mt-8 space-y-6">
            <AnalyticsSummary metrics={metrics} revenueSeries={revenueSeries} retentionSeries={retentionSeries} />
          </div>
        )}
      </section>

      <section className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl">
        <h2 className="text-2xl font-semibold text-white">Son Aktivite</h2>
        <p className="mt-2 text-sm text-slate-400">
          API istek hacimlerini ve abonelik değişikliklerini kontrol ederek altyapınızın sağlıklı
          çalıştığından emin olun.
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-700 bg-slate-950 p-5">
            <p className="text-xs uppercase tracking-widest text-slate-400">API İstekleri</p>
            <p className="mt-2 text-3xl font-bold text-white">1.2M</p>
            <p className="text-sm text-emerald-400">Son 24 saatte +14%</p>
          </div>
          <div className="rounded-2xl border border-slate-700 bg-slate-950 p-5">
            <p className="text-xs uppercase tracking-widest text-slate-400">Yeni Kurumlar</p>
            <p className="mt-2 text-3xl font-bold text-white">32</p>
            <p className="text-sm text-emerald-400">Haftalık +6</p>
          </div>
          <div className="rounded-2xl border border-slate-700 bg-slate-950 p-5">
            <p className="text-xs uppercase tracking-widest text-slate-400">Churn</p>
            <p className="mt-2 text-3xl font-bold text-white">1.8%</p>
            <p className="text-sm text-rose-400">Önceki aya göre -0.3%</p>
          </div>
        </div>
      </section>
    </div>
  );
};
