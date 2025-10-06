import React from "react";
import { api } from "../../api/client.js";
import { Link } from "react-router-dom";
import { trackEvent } from "../../utils/telemetry.js";

export default function HoldingsRecalculate() {
  const [date, setDate] = React.useState(() => {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  });
  const [loading, setLoading] = React.useState(false);
  const [message, setMessage] = React.useState("");
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    trackEvent("page_view", { page: "holdings_recalculate" });
  }, []);

  const onRecalc = async () => {
    setMessage("");
    setError("");
    setLoading(true);
    trackEvent("recalc_holdings_click", { date });
    try {
      const res = await api.recalcHoldings(date);
      const del = res?.deleted ?? 0;
      const ins = res?.inserted ?? 0;
      setMessage(`Recalculated holdings for ${res?.date || date}. Deleted ${del}, Inserted ${ins}.`);
      trackEvent("recalc_holdings_success", { date: res?.date || date, deleted: del, inserted: ins });
    } catch (e) {
      setError(e?.message || "Failed to recalculate holdings.");
      trackEvent("recalc_holdings_error", { message: e?.message || String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Recalculate Holdings</h1>
      <div style={{ background: "white", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", display: "grid", gap: 12, maxWidth: 520 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Date</span>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
        </label>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button type="button" onClick={onRecalc} disabled={loading || !date} style={{ background: loading ? "#94a3b8" : "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: loading ? "not-allowed" : "pointer" }}>
            {loading ? "Recalculating..." : "Recalculate"}
          </button>
          <Link to="/holdings" style={{ background: "#e2e8f0", color: "#0f172a", border: "none", padding: "10px 12px", borderRadius: 8, textDecoration: "none" }}>Back to Holdings</Link>
        </div>
        {message && <div style={{ color: "#0f766e" }}>{message}</div>}
        {error && <div style={{ color: "#b91c1c" }}>{error}</div>}
      </div>
    </div>
  );
}
