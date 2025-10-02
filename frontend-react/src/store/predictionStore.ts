import { create } from 'zustand';
import { client, withErrorHandling } from '@/api/client';

export interface Prediction {
  id: string;
  asset: string;
  predictedPrice: number;
  confidence: number;
  createdAt: string;
}

interface PredictionState {
  predictions: Prediction[];
  latestPrice: Record<string, number>;
  isLoading: boolean;
  error: string | null;
  fetchPredictions: () => Promise<void>;
  addPrediction: (prediction: Prediction) => void;
  updateLivePrice: (asset: string, price: number) => void;
  clear: () => void;
}

export const usePredictionStore = create<PredictionState>((set) => ({
  predictions: [],
  latestPrice: {},
  isLoading: false,
  error: null,
  async fetchPredictions() {
    set({ isLoading: true, error: null });
    try {
      const data = await withErrorHandling<Prediction[]>(() => client.get('/predictions/latest'));
      set({ predictions: data, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch predictions';
      set({ error: message, isLoading: false });
    }
  },
  addPrediction(prediction) {
    set((state) => ({
      predictions: [prediction, ...state.predictions].slice(0, 20),
    }));
  },
  updateLivePrice(asset, price) {
    set((state) => ({
      latestPrice: {
        ...state.latestPrice,
        [asset]: price,
      },
    }));
  },
  clear() {
    set({ predictions: [], latestPrice: {}, error: null });
  },
}));
