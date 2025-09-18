import { io } from "socket.io-client";
import { useEffect } from "react";
import { useApp } from "./store";

const socket = io("/", { path: "/socket.io", transports: ["websocket"] });

export default function App() {
  const { connected, setConnected, lastMessage, setLastMessage } = useApp();

  useEffect(() => {
    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
    socket.on("server_welcome", (p: any) => setLastMessage(p?.msg ?? "welcome"));
    return () => {
      socket.off("connect");
      socket.off("disconnect");
      socket.off("server_welcome");
    };
  }, [setConnected, setLastMessage]);

  return (
    <main className="min-h-screen">
      <header className="px-6 py-4 border-b border-white/10 backdrop-blur sticky top-0">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold">OrcaQuant</h1>
          <div className={`text-sm ${connected ? "text-emerald-400" : "text-red-400"}`}>
            {connected ? "Real-time bağlı" : "Bağlı değil"}
          </div>
        </div>
      </header>
      <section className="max-w-6xl mx-auto px-6 py-12 grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-3xl font-semibold mb-3">Akıllı DeFi Analiz</h2>
          <p className="text-white/70">
            Gerçek zamanlı bildirimler, WebSocket bağlantısı, gelişmiş panel ve performans odaklı SPA mimarisi.
          </p>
          <div className="mt-6 p-4 rounded-xl border border-white/10">
            <div className="text-white/80">Sunucudan mesaj:</div>
            <div className="text-2xl mt-1">{lastMessage ?? "—"}</div>
          </div>
          <div className="mt-6 flex gap-3">
            <a href="/privacy" className="underline">Gizlilik</a>
            <a href="/terms" className="underline">Kullanım Şartları</a>
          </div>
        </div>
        <div className="rounded-2xl border border-white/10 p-6">
          <h3 className="text-xl mb-2">Durum</h3>
          <ul className="space-y-1 text-white/80">
            <li>Health: <code>/healthz</code></li>
            <li>Metrics: <code>/metrics</code></li>
            <li>API: <code>/api/ping</code></li>
            <li>WebSocket Path: <code>/socket.io</code></li>
          </ul>
        </div>
      </section>
    </main>
  );
}
