interface SubscriptionCardProps {
  title: string;
  price: string;
  description: string;
  features: readonly string[];
  ctaLabel: string;
  highlighted?: boolean;
}

export const SubscriptionCard = ({
  title,
  price,
  description,
  features,
  ctaLabel,
  highlighted = false,
}: SubscriptionCardProps): JSX.Element => {
  const baseClasses = [
    'relative flex h-full flex-col rounded-2xl border p-6 shadow-xl transition',
    'hover:-translate-y-1',
    highlighted ? 'border-accent/60 bg-slate-900/90 shadow-accent/20' : 'border-slate-800 bg-slate-900/60',
  ].join(' ');

  const buttonClasses = [
    'mt-8 rounded-xl px-5 py-3 text-sm font-semibold transition focus:outline-none',
    'focus-visible:ring-2 focus-visible:ring-accent/70',
    highlighted
      ? 'bg-accent text-slate-900 shadow-lg shadow-accent/20 hover:bg-cyan-400'
      : 'bg-slate-800 text-white hover:bg-slate-700',
  ].join(' ');

  return (
    <div className={baseClasses}>
      {highlighted && (
        <span className="absolute right-4 top-4 rounded-full bg-accent/20 px-3 py-1 text-xs font-semibold uppercase text-accent">
          Popüler
        </span>
      )}
      <h3 className="text-xl font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm text-slate-400">{description}</p>
      <p className="mt-6 text-4xl font-bold text-white">
        {price}
        <span className="text-base font-normal text-slate-400"> /ay</span>
      </p>
      <ul className="mt-6 space-y-3 text-sm text-slate-200">
        {features.map((feature) => (
          <li key={feature} className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-accent/20 text-accent">✓</span>
            {feature}
          </li>
        ))}
      </ul>
      <button type="button" className={buttonClasses}>
        {ctaLabel}
      </button>
    </div>
  );
};
