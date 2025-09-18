import * as React from "react";

export default function Market() {
  const [rows, setRows] = React.useState<any[]>([]);
  React.useEffect(() => {
    fetch("/api/v2/market/top?limit=10")
      .then((r) => r.json())
      .then((j) => setRows(j.data || []));
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <h2>Top 10 (v2)</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))",
          gap: 12
        }}
      >
        {rows.map((c: any) => (
          <div
            key={c.id}
            style={{
              border: "1px solid #24314d",
              borderRadius: 12,
              padding: 12,
              background: "#0f172a",
              color: "#fff"
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontWeight: 700
              }}
            >
              <span>{c.name}</span>
              <span>${Number(c.current_price || 0).toLocaleString()}</span>
            </div>
            <div style={{ fontSize: 12, opacity: 0.7, marginTop: 4 }}>
              {String(c.symbol || "").toUpperCase()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
