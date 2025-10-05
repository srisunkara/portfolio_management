import React from "react";
import { api } from "../../api/client.js";

export default function PortfolioAdminDownloadPrices() {
  const [date, setDate] = React.useState(() => new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState(null);
  const [error, setError] = React.useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const res = await api.downloadPrices(date);
      setResult(res);
    } catch (e) {
      setError(e?.message || "Failed to download prices");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Download Prices (Yahoo)</h1>
      <form onSubmit={onSubmit} style={{ background: "white", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", display: "grid", gap: 12, maxWidth: 560 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Date</span>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="submit" disabled={loading} style={{ background: loading ? "#94a3b8" : "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: loading ? "not-allowed" : "pointer" }}>
            {loading ? "Downloading..." : "Download Prices"}
          </button>
        </div>
        {error && <div style={{ color: "#b91c1c" }}>{error}</div>}
        {result && (
          <div style={{ background: "#f1f5f9", padding: 12, borderRadius: 8 }}>
            <div><strong>Date:</strong> {result.date}</div>
            <div><strong>Attempted:</strong> {result.attempted}</div>
            <div><strong>Saved:</strong> {result.saved}</div>
            <div><strong>Skipped:</strong> {result.skipped}</div>
            {Array.isArray(result.errors) && result.errors.length > 0 && (
              <details style={{ marginTop: 8 }}>
                <summary>Errors ({result.errors.length})</summary>
                <ul>
                  {result.errors.map((err, idx) => (
                    <li key={idx} style={{ color: "#b91c1c" }}>{typeof err === "string" ? err : JSON.stringify(err)}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}
      </form>
    </div>
  );
}
