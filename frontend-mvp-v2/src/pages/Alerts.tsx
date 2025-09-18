import * as React from "react";

export default function Alerts() {
  const [list, setList] = React.useState<any[]>([]);
  const [form, setForm] = React.useState({
    type: "price_below",
    symbol: "BTC",
    threshold: 60000,
    cooldown_sec: 1800
  });

  async function create() {
    await fetch("/api/v2/alerts", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });
    await reload();
  }

  async function reload() {
    const r = await fetch("/api/v2/alerts", { credentials: "include" });
    setList(await r.json());
  }

  React.useEffect(() => {
    reload();
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <h2>Uyarılar (v2)</h2>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <select
          value={form.type}
          onChange={(e) => setForm({ ...form, type: e.target.value })}
        >
          <option value="price_below">Fiyat Altında</option>
          <option value="price_above">Fiyat Üstünde</option>
          <option value="rsi_below">RSI Altında</option>
          <option value="rsi_above">RSI Üstünde</option>
        </select>
        <input
          value={form.symbol}
          onChange={(e) =>
            setForm({ ...form, symbol: e.target.value.toUpperCase() })
          }
        />
        <input
          type="number"
          value={form.threshold}
          onChange={(e) =>
            setForm({ ...form, threshold: Number(e.target.value) })
          }
        />
        <button onClick={create}>Ekle</button>
      </div>
      <ul>
        {list.map((x) => (
          <li key={x.id}>
            <code>{JSON.stringify(x)}</code>
          </li>
        ))}
      </ul>
    </div>
  );
}
