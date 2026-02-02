import { LimitsPayload } from '@/hooks/usePlanLimits';

const gradientForUsage = (percent: number): string => {
  if (percent >= 100) return 'bg-gradient-to-r from-rose-600 to-rose-700';
  if (percent >= 90) return 'bg-gradient-to-r from-amber-500 to-orange-500';
  if (percent >= 75) return 'bg-gradient-to-r from-yellow-400 to-amber-400';
  return 'bg-gradient-to-r from-emerald-500 to-cyan-500';
};

export const PlanUsagePanel = ({ data }: { data: LimitsPayload }): JSX.Element => {
  const planName = data.plan ?? 'Bilinmeyen Plan';
  const entries = Object.entries(data.limits ?? {});

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Aktif Plan</p>
          <h3 className="text-2xl font-semibold text-white">{planName}</h3>
          <p className="text-sm text-slate-400">Günlük kullanım haklarınızı gerçek zamanlı takip edin.</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-300">
          {entries.length} özellik izleniyor
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {entries.map(([key, item]) => (
          <div key={key} className="space-y-2 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold text-white">{key}</p>
                <p className="text-xs text-slate-400">{item.used} / {item.limit} kullanım</p>
              </div>
              {item.exhausted ? (
                <span className="rounded-full bg-rose-500/20 px-3 py-1 text-xs font-semibold text-rose-100">Tükendi</span>
              ) : item.warn_90 ? (
                <span className="rounded-full bg-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-100">%90+</span>
              ) : item.warn_75 ? (
                <span className="rounded-full bg-yellow-400/20 px-3 py-1 text-xs font-semibold text-yellow-900">%75+</span>
              ) : (
                <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-100">Sağlıklı</span>
              )}
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className={`${gradientForUsage(item.percent_used)} h-full rounded-full transition-all`}
                style={{ width: `${Math.min(item.percent_used, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
