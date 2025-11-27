import { useEffect } from 'react';
import { X } from 'lucide-react';
import { useToastStore } from '@/store/toastStore';

const variantStyles: Record<string, string> = {
  info: 'bg-slate-800 border-slate-600 text-slate-100',
  warning: 'bg-amber-900/80 border-amber-500 text-amber-50',
  error: 'bg-rose-900/80 border-rose-500 text-rose-50',
  success: 'bg-emerald-900/80 border-emerald-500 text-emerald-50',
};

export const ToastCenter = (): JSX.Element | null => {
  const { toasts, dismiss } = useToastStore();

  useEffect(() => {
    if (toasts.length === 0) return;
    const timers = toasts.map((toast) => setTimeout(() => dismiss(toast.id), 6000));
    return () => timers.forEach(clearTimeout);
  }, [toasts, dismiss]);

  if (!toasts.length) return null;

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-md flex-col gap-3">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex items-start gap-3 rounded-2xl border px-4 py-3 shadow-2xl ${
            variantStyles[toast.variant] ?? variantStyles.info
          }`}
        >
          <div className="mt-0.5 text-sm leading-relaxed">{toast.message}</div>
          <button
            type="button"
            aria-label="Toastı kapat"
            onClick={() => dismiss(toast.id)}
            className="ml-auto text-xs text-slate-300 transition hover:text-white"
          >
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
};
