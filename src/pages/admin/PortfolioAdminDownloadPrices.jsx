import React from "react";
import { api } from "../../api/client.js";
import { trackEvent } from "../../utils/telemetry.js";

export default function PortfolioAdminDownloadPrices() {
  // Date range states with defaults to last work day and today
  const [fromDate, setFromDate] = React.useState(() => {
    // Default to last work day (Fri if weekend)
    const d = new Date();
    const day = d.getDay(); // 0=Sun,6=Sat
    const delta = day === 0 ? 2 : day === 6 ? 1 : 0;
    d.setDate(d.getDate() - delta);
    return d.toISOString().slice(0, 10);
  });
  const [toDate, setToDate] = React.useState(() => {
    // Default to today
    return new Date().toISOString().slice(0, 10);
  });
  const [ticker, setTicker] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState(null);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    trackEvent("page_view", { page: "download_prices" });
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    trackEvent("download_prices_click", { fromDate, toDate, ticker });
    try {
      // Convert ticker filter to array if provided
      const tickers = ticker.trim() ? ticker.split(',').map(t => t.trim()).filter(t => t) : null;
      const res = await api.downloadPrices(fromDate, toDate, tickers);
      setResult(res);
      trackEvent("download_prices_success", { 
        fromDate, 
        toDate, 
        ticker,
        added_count: res?.added?.count, 
        skipped_count: res?.skipped?.count, 
        failed_count: res?.failed?.count 
      });
    } catch (e) {
      setError(e?.message || "Failed to download prices");
      trackEvent("download_prices_error", { message: e?.message || String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Download Prices (Yahoo)</h1>
      <form onSubmit={onSubmit} style={{ background: "white", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", display: "grid", gap: 12, maxWidth: 560 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>From Date</span>
            <input 
              type="date" 
              value={fromDate} 
              onChange={(e) => setFromDate(e.target.value)} 
              required 
              style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} 
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>To Date</span>
            <input 
              type="date" 
              value={toDate} 
              onChange={(e) => setToDate(e.target.value)} 
              required 
              style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} 
            />
          </label>
        </div>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Tickers (Optional)</span>
          <input 
            type="text" 
            value={ticker} 
            onChange={(e) => setTicker(e.target.value)} 
            placeholder="e.g. VOO,AAPL,MSFT (comma-separated, leave empty for all securities)"
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} 
          />
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="submit" disabled={loading} style={{ background: loading ? "#94a3b8" : "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: loading ? "not-allowed" : "pointer" }}>
            {loading ? "Downloading..." : "Download Prices"}
          </button>
        </div>
        {error && <div style={{ color: "#b91c1c" }}>{error}</div>}
        {result && (
          <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: 12, marginTop: 12 }}>
            <h3 style={{ margin: "0 0 8px 0", color: "#166534" }}>Download Results Summary</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, fontSize: "14px", marginBottom: 12 }}>
              <div><strong>Date Range:</strong> {result.from_date} to {result.to_date}</div>
              <div><strong>Business Days:</strong> {result.business_days}</div>
            </div>
            
            {/* Added Securities */}
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: "bold", color: "#166534", marginBottom: 4 }}>
                Added ({result.added?.count || 0} tickers)
              </div>
              {result.added?.tickers && result.added.tickers.length > 0 ? (
                <div style={{ fontSize: "12px", color: "#374151", backgroundColor: "#f3f4f6", padding: 8, borderRadius: 4, maxHeight: "100px", overflow: "auto" }}>
                  {result.added.tickers.join(", ")}
                </div>
              ) : (
                <div style={{ fontSize: "12px", color: "#6b7280" }}>No tickers added</div>
              )}
            </div>

            {/* Skipped Securities */}
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: "bold", color: "#d97706", marginBottom: 4 }}>
                Skipped ({result.skipped?.count || 0} tickers)
              </div>
              {result.skipped?.tickers && result.skipped.tickers.length > 0 ? (
                <div style={{ fontSize: "12px", color: "#374151", backgroundColor: "#fef3c7", padding: 8, borderRadius: 4, maxHeight: "100px", overflow: "auto" }}>
                  {result.skipped.tickers.join(", ")}
                </div>
              ) : (
                <div style={{ fontSize: "12px", color: "#6b7280" }}>No tickers skipped</div>
              )}
            </div>

            {/* Failed Securities */}
            {result.failed?.count > 0 && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontWeight: "bold", color: "#dc2626", marginBottom: 4 }}>
                  Failed ({result.failed.count} tickers)
                </div>
                <div style={{ fontSize: "12px", color: "#374151", backgroundColor: "#fee2e2", padding: 8, borderRadius: 4, maxHeight: "100px", overflow: "auto" }}>
                  {result.failed.tickers.join(", ")}
                </div>
              </div>
            )}
          </div>
        )}
      </form>
    </div>
  );
}
