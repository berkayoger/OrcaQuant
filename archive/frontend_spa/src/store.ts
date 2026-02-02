import { create } from "zustand";

type State = {
  connected: boolean;
  lastMessage?: string;
  setConnected: (v: boolean) => void;
  setLastMessage: (s?: string) => void;
};

export const useApp = create<State>((set) => ({
  connected: false,
  lastMessage: undefined,
  setConnected: (v) => set({ connected: v }),
  setLastMessage: (s) => set({ lastMessage: s }),
}));
