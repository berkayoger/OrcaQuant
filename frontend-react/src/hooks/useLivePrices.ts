import { useEffect, useRef } from 'react';
import { usePredictionStore } from '@/store/predictionStore';

interface PriceMessage {
  asset: string;
  price: number;
  timestamp: string;
}

export const useLivePrices = (enabled: boolean = true): void => {
  const updateLivePrice = usePredictionStore((state) => state.updateLivePrice);
  const addPrediction = usePredictionStore((state) => state.addPrediction);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    const wsUrl = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws/prices';
    socketRef.current = new WebSocket(wsUrl);

    socketRef.current.onmessage = (event) => {
      try {
        const data: PriceMessage = JSON.parse(event.data);
        if (!data.asset || typeof data.price !== 'number') {
          return;
        }
        updateLivePrice(data.asset, data.price);
        addPrediction({
          id: `${data.asset}-${data.timestamp}`,
          asset: data.asset,
          predictedPrice: data.price,
          confidence: 0.8,
          createdAt: data.timestamp,
        });
      } catch (error) {
        console.error('Failed to parse WebSocket message', error);
      }
    };

    socketRef.current.onerror = (event) => {
      console.error('WebSocket error', event);
    };

    return () => {
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [addPrediction, enabled, updateLivePrice]);
};
