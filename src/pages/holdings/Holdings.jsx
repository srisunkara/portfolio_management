import React from "react";
import { api } from "../../api/client.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { trackEvent } from "../../utils/telemetry.js";

export default function Holdings() {
  const [data, setData] = React.useState([]);
  const [filters, setFilters] = React.useState({});
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const { user } = useAuth();
  const [myPortfolioIds, setMyPortfolioIds] = React.useState([]);
  const [portfolioMap, setPortfolioMap] = React.useState({});
  const [securityMap, setSecurityMap] = React.useState({});

  React.useEffect(() => {
    let isMounted = true;
    trackEvent("page_view", { page: "holdings_list" });
    (async () => {
      try {
        const [res, portfolios, securities] = await Promise.all([
          api.getHoldings(),
          api.listPortfolios(),
          api.listSecurities(),
        ]);
        const uid = user?.user_id || user?.id || user?.userId;
        const mineIds = uid ? (portfolios || []).filter(p=>p.user_id === uid).map(p=>p.portfolio_id) : (portfolios || []).map(p=>p.portfolio_id);
        const pmap = Object.fromEntries((portfolios||[]).map(p => [p.portfolio_id, p.name]));
        const smap = Object.fromEntries((securities||[]).map(s => [s.security_id, s.name || s.ticker]));
        if (isMounted) {
          setMyPortfolioIds(mineIds);
          setPortfolioMap(pmap);
          setSecurityMap(smap);
          setData(res);
          // Default date filter to yesterday
          const d = new Date();
          d.setDate(d.getDate() - 1);
          const yyyy = d.getFullYear();
          const mm = String(d.getMonth() + 1).padStart(2, "0");
          const dd = String(d.getDate()).padStart(2, "0");
          setFilters(prev => ({ ...prev, holding_dt: `${yyyy}-${mm}-${dd}` }));
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
      // security_price_dt filter
      const spdt = h.security_price_dt;
      const spdtStr = typeof spdt === "string" && /^\d{4}-\d{2}-\d{2}$/.test(spdt)
        ? spdt
        : (spdt ? (() => { const d = new Date(spdt); if (Number.isNaN(d.getTime())) return String(spdt); const yyyy=d.getFullYear(); const mm=String(d.getMonth()+1).padStart(2,'0'); const dd=String(d.getDate()).padStart(2,'0'); return `${yyyy}-${mm}-${dd}`; })() : "");
      const fspdt = filters.security_price_dt ?? "";
      checks.push(!fspdt || spdtStr === fspdt);
      checks.push(String(h.portfolio_id ?? "").toLowerCase().includes(String(filters.portfolio_id ?? "").toLowerCase()));
      checks.push(String(h.security_id ?? "").toLowerCase().includes(String(filters.security_id ?? "").toLowerCase()));
      // Name filters
      const pName = portfolioMap[h.portfolio_id] || "";
      const sName = securityMap[h.security_id] || "";
      const pf = (filters.portfolio_name || "").toLowerCase();
      const sf = (filters.security_name || "").toLowerCase();
      checks.push(!pf || String(pName).toLowerCase().includes(pf));
      checks.push(!sf || String(sName).toLowerCase().includes(sf));
      // Numeric filters
      checks.push(compareNumberWithOp(h.quantity, filters.quantity ?? ""));
      checks.push(compareNumberWithOp(h.price, filters.price ?? ""));
      checks.push(compareNumberWithOp(h.avg_price, filters.avg_price ?? ""));
      checks.push(compareNumberWithOp(h.market_value, filters.market_value ?? ""));
      checks.push(compareNumberWithOp(h.holding_cost_amt, filters.holding_cost_amt ?? ""));
      checks.push(compareNumberWithOp(h.unreal_gain_loss_amt, filters.unreal_gain_loss_amt ?? ""));
      checks.push(compareNumberWithOp(h.unreal_gain_loss_perc, filters.unreal_gain_loss_perc ?? ""));
      return checks.every(Boolean);
    });
  }, [data, filters, myPortfolioIds, portfolioMap, securityMap]);

  // Number formatter for table numeric cells
  const fmt = (val, digits = 2) => {
    const num = typeof val === "number" ? val : Number(val);
    if (!Number.isFinite(num)) return val ?? "-";
    try {
      return num.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
    } catch (e) {
      return num.toFixed(digits);
    }
  };

  if (loading) return <div>Loading holdings...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Holdings</h1>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span>Date</span>
          <input type="date" value={filters.holding_dt ?? ""} onChange={(e)=>onFilterChange("holding_dt", e.target.value)} style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1" }} />
        </label>
        <button
          type="button"
          onClick={clearFilters}
          style={{ background: "#e2e8f0", color: "#0f172a", padding: "8px 12px", borderRadius: 8, border: "none", cursor: "pointer" }}
        >
          Clear Filters
        </button>
      </div>
      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflow: "auto", maxHeight: "calc(100vh - 160px)", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 1100 }}>
          <thead style={{ background: "#f1f5f9", position: "sticky", top: 0, zIndex: 5 }}>
            <tr>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Holding Dt</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Portfolio Name</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Security Name</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Quantity</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Price</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Avg Price</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Holding Cost Amt</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Market Value</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Unreal GL Amt</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Unreal GL %</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Security Price Dt</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Holding Id</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Portfolio Id</th>
              <th style={{ textAlign: "left", padding: 12, position: "sticky", top: 0, background: "#f1f5f9" }}>Security Id</th>
            </tr>
            <tr>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="date" value={filters.holding_dt ?? ""} onChange={(e)=>onFilterChange("holding_dt", e.target.value)} style={{ width: "100%", maxWidth: 140, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="Filter name" value={filters.portfolio_name ?? ""} onChange={(e)=>onFilterChange("portfolio_name", e.target.value)} style={{ width: "100%", maxWidth: 180, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="Filter name" value={filters.security_name ?? ""} onChange={(e)=>onFilterChange("security_name", e.target.value)} style={{ width: "100%", maxWidth: 200, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="e.g. >0" value={filters.quantity ?? ""} onChange={(e)=>onFilterChange("quantity", e.target.value)} style={{ width: "100%", maxWidth: 120, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="e.g. >=1" value={filters.price ?? ""} onChange={(e)=>onFilterChange("price", e.target.value)} style={{ width: "100%", maxWidth: 120, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="e.g. >=1" value={filters.avg_price ?? ""} onChange={(e)=>onFilterChange("avg_price", e.target.value)} style={{ width: "100%", maxWidth: 120, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="e.g. >1000" value={filters.holding_cost_amt ?? ""} onChange={(e)=>onFilterChange("holding_cost_amt", e.target.value)} style={{ width: "100%", maxWidth: 140, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="e.g. >1000" value={filters.market_value ?? ""} onChange={(e)=>onFilterChange("market_value", e.target.value)} style={{ width: "100%", maxWidth: 140, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="e.g. >0" value={filters.unreal_gain_loss_amt ?? ""} onChange={(e)=>onFilterChange("unreal_gain_loss_amt", e.target.value)} style={{ width: "100%", maxWidth: 140, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" placeholder="e.g. >0" value={filters.unreal_gain_loss_perc ?? ""} onChange={(e)=>onFilterChange("unreal_gain_loss_perc", e.target.value)} style={{ width: "100%", maxWidth: 120, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="date" value={filters.security_price_dt ?? ""} onChange={(e)=>onFilterChange("security_price_dt", e.target.value)} style={{ width: "100%", maxWidth: 140, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" value={filters.holding_id ?? ""} onChange={(e)=>onFilterChange("holding_id", e.target.value)} style={{ width: "100%", maxWidth: 140, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" value={filters.portfolio_id ?? ""} onChange={(e)=>onFilterChange("portfolio_id", e.target.value)} style={{ width: "100%", maxWidth: 120, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
              <th style={{ textAlign: "left", padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }}>
                <input type="text" value={filters.security_id ?? ""} onChange={(e)=>onFilterChange("security_id", e.target.value)} style={{ width: "100%", maxWidth: 120, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }} />
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((h, idx) => (
              <tr key={h.holding_id ?? JSON.stringify(h)} style={{ borderTop: "1px solid #e2e8f0", background: idx % 2 === 1 ? "#f8fafc" : "white" }}>
                {/* Align cells with headers: Holding Dt, Portfolio Name, Security Name, Quantity, Price, Avg Price, Holding Cost Amt, Market Value, Unreal GL Amt, Unreal GL %, Security Price Dt, Holding Id, Portfolio Id, Security Id */}
                <td style={{ padding: 12 }}>{h.holding_dt}</td>
                <td style={{ padding: 12 }}>{portfolioMap[h.portfolio_id] || "-"}</td>
                <td style={{ padding: 12 }}>{securityMap[h.security_id] || "-"}</td>
                <td style={{ padding: 12 }}>{fmt(h.quantity)}</td>
                <td style={{ padding: 12 }}>{fmt(h.price)}</td>
                <td style={{ padding: 12 }}>{fmt(h.avg_price)}</td>
                <td style={{ padding: 12 }}>{fmt(h.holding_cost_amt)}</td>
                <td style={{ padding: 12 }}>{fmt(h.market_value)}</td>
                <td style={{ padding: 12 }}>{fmt(h.unreal_gain_loss_amt)}</td>
                <td style={{ padding: 12 }}>{fmt(h.unreal_gain_loss_perc)}</td>
                <td style={{ padding: 12 }}>{h.security_price_dt || "-"}</td>
                {/* Identifier columns at the end */}
                <td style={{ padding: 12 }}>{h.holding_id}</td>
                <td style={{ padding: 12 }}>{h.portfolio_id}</td>
                <td style={{ padding: 12 }}>{h.security_id}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan="14" style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                  No holdings found.
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            {(() => {
              // compute totals for numeric columns
              let totals = {
                quantity: 0,
                price: 0,
                avg_price: 0,
                holding_cost_amt: 0,
                market_value: 0,
                unreal_gain_loss_amt: 0,
                unreal_gain_loss_perc: 0,
              };
              filtered.forEach(h => {
                const add = (k, v) => { const num = Number(v); if (Number.isFinite(num)) totals[k] += num; };
                add('quantity', h.quantity);
                add('price', h.price);
                add('avg_price', h.avg_price);
                add('holding_cost_amt', h.holding_cost_amt);
                add('market_value', h.market_value);
                add('unreal_gain_loss_amt', h.unreal_gain_loss_amt);
                add('unreal_gain_loss_perc', h.unreal_gain_loss_perc);
              });
              const fmt = (n) => Number.isFinite(n) ? n.toLocaleString(undefined,{minimumFractionDigits:2, maximumFractionDigits:2}) : n;
              return (
                <tr style={{ borderTop: "2px solid #e2e8f0", background: "#f8fafc", fontWeight: 700 }}>
                  {/* Span first 3 non-numeric columns so totals line up under Quantity */}
                  <td style={{ padding: 12 }} colSpan={3}>Totals ({filtered.length})</td>
                  <td style={{ padding: 12 }}>{fmt(totals.quantity)}</td>
                  <td style={{ padding: 12 }}>{fmt(totals.price)}</td>
                  <td style={{ padding: 12 }}>{fmt(totals.avg_price)}</td>
                  <td style={{ padding: 12 }}>{fmt(totals.holding_cost_amt)}</td>
                  <td style={{ padding: 12 }}>{fmt(totals.market_value)}</td>
                  <td style={{ padding: 12 }}>{fmt(totals.unreal_gain_loss_amt)}</td>
                  <td style={{ padding: 12 }}>{fmt(totals.unreal_gain_loss_perc)}</td>
                  {/* Remaining columns: Security Price Dt + 3 identifiers */}
                  <td colSpan={4} />
                </tr>
              );
            })()}
          </tfoot>
        </table>
      </div>
    </div>
  );
}