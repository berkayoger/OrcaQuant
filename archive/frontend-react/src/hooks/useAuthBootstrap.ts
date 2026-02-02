import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';

export const useAuthBootstrap = (): void => {
  const setHydrated = useAuthStore((state) => state.setHydrated);

  useEffect(() => {
    setHydrated();
  }, [setHydrated]);
};
