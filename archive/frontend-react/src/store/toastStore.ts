import { create } from 'zustand';

export type ToastVariant = 'info' | 'warning' | 'error' | 'success';

export interface ToastMessage {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastState {
  toasts: ToastMessage[];
  push: (message: string, variant?: ToastVariant) => void;
  dismiss: (id: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (message, variant = 'info') =>
    set((state) => ({
      toasts: [...state.toasts, { id: crypto.randomUUID(), message, variant }],
    })),
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) })),
}));
