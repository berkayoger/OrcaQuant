import { create } from 'zustand';
import { client, withErrorHandling } from '@/api/client';

export interface AnalyticsMetric {
  label: string;
  value: number;
  change: number;
}

export interface AnalyticsPoint {
  timestamp: string;
  value: number;
}

interface AdminAnalyticsState {
  metrics: AnalyticsMetric[];
  revenueSeries: AnalyticsPoint[];
  retentionSeries: AnalyticsPoint[];
  isLoading: boolean;
  error: string | null;
  fetchAnalytics: () => Promise<void>;
}

export const useAdminAnalyticsStore = create<AdminAnalyticsState>((set) => ({
  metrics: [],
  revenueSeries: [],
  retentionSeries: [],
  isLoading: false,
  error: null,
  async fetchAnalytics() {
    set({ isLoading: true, error: null });
    try {
      const data = await withErrorHandling<{ metrics: AnalyticsMetric[]; revenue: AnalyticsPoint[]; retention: AnalyticsPoint[] }>(
        () => client.get('/admin/analytics'),
      );
      set({
        metrics: data.metrics,
        revenueSeries: data.revenue,
        retentionSeries: data.retention,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch admin analytics';
      set({ error: message, isLoading: false });
    }
  },
}));
