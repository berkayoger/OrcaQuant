import { useEffect, useState } from 'react';
import { client, withErrorHandling } from '@/api/client';
import { useToastStore } from '@/store/toastStore';

export interface LimitUsage {
  limit: number;
  used: number;
  remaining: number;
  percent_used: number;
  warn_75: boolean;
  warn_90: boolean;
  exhausted: boolean;
}

export interface LimitsPayload {
  plan?: string | null;
  limits: Record<string, LimitUsage>;
}

export const usePlanLimits = (): { data: LimitsPayload | null; loading: boolean } => {
  const push = useToastStore((state) => state.push);
  const [data, setData] = useState<LimitsPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchLimits = async (): Promise<void> => {
      try {
        const response = await withErrorHandling<LimitsPayload>(() => client.get('/limits/status'));
        setData(response);
      } catch (error) {
        push((error as Error).message ?? 'Limit bilgisi alınamadı', 'warning');
      } finally {
        setLoading(false);
      }
    };

    fetchLimits();
  }, [push]);

  return { data, loading };
};
