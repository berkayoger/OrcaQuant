import * as React from "react";

export default function Indicators() {
  const [input, setInput] = React.useState(
    "100,101,99,102,103,100,98,97,96,97,99,101,102,103,104,105,104,103,104"
  );
  const [out, setOut] = React.useState<any>(null);

  async function run() {
    const arr = input
      .split(",")
      .map((x) => Number(x.trim()))
      .filter(Boolean);
    const r = await fetch("/api/v2/indicators/basic", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prices: arr })
    });
    setOut(await r.json());
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>Indicators (v2)</h2>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        rows={4}
        style={{ width: "100%" }}
      />
      <button onClick={run} style={{ marginTop: 8 }}>
        Hesapla
      </button>
      <pre>{out && JSON.stringify(out, null, 2)}</pre>
    </div>
  );
}
