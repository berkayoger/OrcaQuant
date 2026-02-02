import * as React from "react";

export default function Portfolio() {
  const [file, setFile] = React.useState<File | null>(null);
  const [summary, setSummary] = React.useState<any>(null);

  async function upload() {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    await fetch("/api/v2/portfolio/import", {
      method: "POST",
      credentials: "include",
      body: fd
    });
    const r = await fetch("/api/v2/portfolio/summary", { credentials: "include" });
    setSummary(await r.json());
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>Portföy (v2)</h2>
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button onClick={upload} style={{ marginLeft: 8 }}>
        Yükle & Özet
      </button>
      <pre>{summary && JSON.stringify(summary, null, 2)}</pre>
    </div>
  );
}
