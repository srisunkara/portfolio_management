import React from "react";
import { api } from "../../api/client.js";
import { useAuth } from "../../context/AuthContext.jsx";

export default function Holdings() {
  const [data, setData] = React.useState([]);
  const [filters, setFilters] = React.useState({});
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const { user } = useAuth();
  const [myPortfolioIds, setMyPortfolioIds] = React.useState([]);

  React.useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const [res, portfolios] = await Promise.all([
          api.getHoldings(),
          api.listPortfolios(),
        ]);
        const uid = user?.user_id || user?.id || user?.userId;
        const mineIds = uid ? (portfolios || []).filter(p=>p.user_id === uid).map(p=>p.portfolio_id) : (portfolios || []).map(p=>p.portfolio_id);
        if (isMounted) {
          setMyPortfolioIds(mineIds);
          setData(res);
        }
      } catch (e) {
        if (isMounted) setError("Failed to load holdings.");
      } finally {
        if (isMounted) setLoading(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, []);

  const onFilterChange = (name, value) => setFilters((prev) => ({ ...prev, [name]: value }));
  const clearFilters = () => setFilters({});

  const compareNumberWithOp = (value, filterStr) => {
    if (filterStr == null || filterStr === "") return true;
    if (value == null || value === "") return false;
    const s = String(filterStr).trim();
    const m = s.match(/^(<=|>=|=|<|>)\s*(-?\d+(?:\.\d+)?)/);
    if (m) {
      const op = m[1];
      const num = parseFloat(m[2]);
      const v = Number(value);
      if (Number.isNaN(v) || Number.isNaN(num)) return false;
      if (op === "=") return v === num;
      if (op === "<") return v < num;
      if (op === "<=") return v <= num;
      if (op === ">") return v > num;
      if (op === ">=") return v >= num;
      return false;
    }
    return String(value).toLowerCase().includes(s.toLowerCase());
  };

  const filtered = React.useMemo(() => {
    const scoped = (myPortfolioIds && myPortfolioIds.length) ? data.filter(h => myPortfolioIds.includes(h.portfolio_id)) : data;
    if (!filters || Object.values(filters).every((v) => !v)) return scoped;
    return scoped.filter((h) => {
      const checks = [];
      checks.push(String(h.holding_id ?? "").toLowerCase().includes(String(filters.holding_id ?? "").toLowerCase()));
      const dt = h.holding_dt;
      const dtStr = typeof dt === "string" && /^\d{4}-\d{2}-\d{2}$/.test(dt)
        ? dt
        : (() => { const d = new Date(dt); if (Number.isNaN(d.getTime())) return String(dt); const yyyy=d.getFullYear(); const mm=String(d.getMonth()+1).padStart(2,'0'); const dd=String(d.getDate()).padStart(2,'0'); return `${yyyy}-${mm}-${dd}`; })();
      const fdt = filters.holding_dt ?? "";
      checks.push(!fdt || dtStr === fdt);
      checks.push(String(h.portfolio_id ?? "").toLowerCase().includes(String(filters.portfolio_id ?? "").toLowerCase()));
      checks.push(String(h.security_id ?? "").toLowerCase().includes(String(filters.security_id ?? "").toLowerCase()));
      checks.push(compareNumberWithOp(h.quantity, filters.quantity ?? ""));
      checks.push(compareNumberWithOp(h.price, filters.price ?? ""));
      checks.push(compareNumberWithOp(h.market_value, filters.market_value ?? ""));
      return checks.every(Boolean);
    });
  }, [data, filters]);

  if (loading) return <div>Loading holdings...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Holdings</h1>
        <button
          type="button"
          onClick={clearFilters}
          style={{ background: "#e2e8f0", color: "#0f172a", padding: "8px 12px", borderRadius: 8, border: "none", cursor: "pointer" }}
        >
          Clear Filters
        </button>
      </div>
      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflow: "auto", maxHeight: "calc(100vh - 140px)", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 720 }}>
          <thead style={{ background: "#f1f5f9" }}>
            <tr>
              <th style={{ textAlign: "left", padding: 12 }}>Holding Id</th>
              <th style={{ textAlign: "left", padding: 12 }}>Holding Dt</th>
              <th style={{ textAlign: "left", padding: 12 }}>Portfolio Id</th>
              <th style={{ textAlign: "left", padding: 12 }}>Security Id</th>
              <th style={{ textAlign: "left", padding: 12 }}>Quantity</th>
              <th style={{ textAlign: "left", padding: 12 }}>Price</th>
              <th style={{ textAlign: "left", padding: 12 }}>Market Value</th>
            </tr>
            <tr>
              <th style={{ textAlign: "left", padding: 8 }}>
                <input type="text" value={filters.holding_id ?? ""} onChange={(e)=>onFilterChange("holding_id", e.target.value)} style={{ width: "100%", maxWidth: 160, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8 }}>
                <input type="date" value={filters.holding_dt ?? ""} onChange={(e)=>onFilterChange("holding_dt", e.target.value)} style={{ width: "100%", maxWidth: 160, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8 }}>
                <input type="text" value={filters.portfolio_id ?? ""} onChange={(e)=>onFilterChange("portfolio_id", e.target.value)} style={{ width: "100%", maxWidth: 160, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8 }}>
                <input type="text" value={filters.security_id ?? ""} onChange={(e)=>onFilterChange("security_id", e.target.value)} style={{ width: "100%", maxWidth: 160, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8 }}>
                <input type="text" placeholder="e.g. >0" value={filters.quantity ?? ""} onChange={(e)=>onFilterChange("quantity", e.target.value)} style={{ width: "100%", maxWidth: 140, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8 }}>
                <input type="text" placeholder="e.g. >=1" value={filters.price ?? ""} onChange={(e)=>onFilterChange("price", e.target.value)} style={{ width: "100%", maxWidth: 140, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8 }}>
                <input type="text" placeholder="e.g. >1000" value={filters.market_value ?? ""} onChange={(e)=>onFilterChange("market_value", e.target.value)} style={{ width: "100%", maxWidth: 160, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((h, idx) => (
              <tr key={h.holding_id ?? JSON.stringify(h)} style={{ borderTop: "1px solid #e2e8f0", background: idx % 2 === 1 ? "#f8fafc" : "white" }}>
                <td style={{ padding: 12 }}>{h.holding_id}</td>
                <td style={{ padding: 12 }}>{h.holding_dt}</td>
                <td style={{ padding: 12 }}>{h.portfolio_id}</td>
                <td style={{ padding: 12 }}>{h.security_id}</td>
                <td style={{ padding: 12 }}>{h.quantity}</td>
                <td style={{ padding: 12 }}>{h.price}</td>
                <td style={{ padding: 12 }}>{h.market_value}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan="7" style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                  No holdings found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}