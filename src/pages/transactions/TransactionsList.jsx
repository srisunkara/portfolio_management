import React from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { getOrderedFields, renderCell, labelize, modelFieldDefs } from "../../models/fields.js";
import { trackEvent } from "../../utils/telemetry.js";
import editImg from "../../images/edit.png";
import deleteImg from "../../images/delete.png";

export default function TransactionsList() {
  const [rows, setRows] = React.useState([]);
  const { user } = useAuth();
  const [fields, setFields] = React.useState([]);
  const [filters, setFilters] = React.useState({});
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  // Sorting state
  const [sortBy, setSortBy] = React.useState(null); // field name
  const [sortDir, setSortDir] = React.useState("asc"); // 'asc' | 'desc'
  // Recalculate fees
  const [recalcLoading, setRecalcLoading] = React.useState(false);
  const [recalcMessage, setRecalcMessage] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    trackEvent("page_view", { page: "transactions_list" });
    (async () => {
      try {
        const f = getOrderedFields("TransactionFullView");
        if (alive) setFields(f);
        const txns = await api.listTransactionsFull();
        const uid = user?.user_id || user?.id || user?.userId;
        const myTxns = uid ? (txns || []).filter(t => t.user_id === uid) : (txns || []);
        if (alive) setRows(myTxns);
      } catch (e) {
        if (alive) setError("Failed to load transactions.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => (alive = false);
  }, []);

  const reloadTransactions = React.useCallback(async () => {
    try {
      const txns = await api.listTransactionsFull();
      const uid = user?.user_id || user?.id || user?.userId;
      const myTxns = uid ? (txns || []).filter(t => t.user_id === uid) : (txns || []);
      setRows(myTxns);
    } catch (e) {
      setError("Failed to load transactions.");
    }
  }, [user]);

  const recalcAllFees = async () => {
    setRecalcMessage("");
    setRecalcLoading(true);
    trackEvent("recalculate_fees_click", { page: "transactions_list" });
    try {
      const res = await api.recalculateTransactionFees();
      const updated = (res && typeof res.updated === "number") ? res.updated : 0;
      setRecalcMessage(`Recalculated fees for ${updated} transactions.`);
      trackEvent("recalculate_fees_success", { updated });
      await reloadTransactions();
    } catch (e) {
      setRecalcMessage(e?.message || "Failed to recalculate fees.");
      trackEvent("recalculate_fees_error", { message: e?.message || String(e) });
    } finally {
      setRecalcLoading(false);
    }
  };

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

  const filteredRows = React.useMemo(() => {
    if (!filters || Object.values(filters).every((v) => !v)) return rows;
    return rows.filter((row) =>
      fields.every((f) => {
        const fv = filters[f.name];
        if (fv == null || fv === "") return true;
        const rv = row[f.name];
        if (f.type === "date") {
          if (!rv) return false;
          const rvStr =
            typeof rv === "string" && /^\d{4}-\d{2}-\d{2}$/.test(rv)
              ? rv
              : (() => {
                  const d = new Date(rv);
                  if (Number.isNaN(d.getTime())) return String(rv);
                  const yyyy = d.getFullYear();
                  const mm = String(d.getMonth() + 1).padStart(2, "0");
                  const dd = String(d.getDate()).padStart(2, "0");
                  return `${yyyy}-${mm}-${dd}`;
                })();
          return rvStr === fv;
        }
        if (f.type === "integer" || f.type === "number") {
          return compareNumberWithOp(rv, fv);
        }
        if (f.type === "boolean") {
          const norm = String(rv === true ? "yes" : rv === false ? "no" : rv).toLowerCase();
          return norm.includes(String(fv).toLowerCase());
        }
        return String(rv ?? "").toLowerCase().includes(String(fv).toLowerCase());
      })
    );
  }, [rows, fields, filters]);

  // Sorted rows based on sortBy and sortDir
  const sortedRows = React.useMemo(() => {
    if (!sortBy) return filteredRows;
    const fieldDef = fields.find((f) => f.name === sortBy);
    const arr = [...filteredRows];
    const dir = sortDir === "desc" ? -1 : 1;
    const safeStr = (v) => String(v ?? "").toLowerCase();
    arr.sort((a, b) => {
      const va = a[sortBy];
      const vb = b[sortBy];
      if (fieldDef?.type === "number" || fieldDef?.type === "integer") {
        const na = Number(va);
        const nb = Number(vb);
        const aa = Number.isFinite(na) ? na : Number.MIN_SAFE_INTEGER;
        const bb = Number.isFinite(nb) ? nb : Number.MIN_SAFE_INTEGER;
        if (aa < bb) return -1 * dir;
        if (aa > bb) return 1 * dir;
        return 0;
      }
      if (fieldDef?.type === "date") {
        const da = va ? new Date(va).getTime() : -Infinity;
        const db = vb ? new Date(vb).getTime() : -Infinity;
        if (da < db) return -1 * dir;
        if (da > db) return 1 * dir;
        return 0;
      }
      if (typeof va === "boolean" || typeof vb === "boolean") {
        const aa = va === true ? 1 : va === false ? 0 : -1;
        const bb = vb === true ? 1 : vb === false ? 0 : -1;
        if (aa < bb) return -1 * dir;
        if (aa > bb) return 1 * dir;
        return 0;
      }
      const sa = safeStr(va);
      const sb = safeStr(vb);
      if (sa < sb) return -1 * dir;
      if (sa > sb) return 1 * dir;
      return 0;
    });
    return arr;
  }, [filteredRows, fields, sortBy, sortDir]);

  const onHeaderClick = (name) => {
    if (sortBy === name) {
      setSortDir((prev) => {
        const next = prev === "asc" ? "desc" : "asc";
        trackEvent("sort_toggle", { page: "transactions_list", field: name, dir: next });
        return next;
      });
    } else {
      setSortBy(name);
      setSortDir("asc");
      trackEvent("sort_toggle", { page: "transactions_list", field: name, dir: "asc" });
    }
  };

  // Summaries for numeric columns over the filtered (and optionally sorted) set
  const totals = React.useMemo(() => {
    const res = {};
    for (const f of fields) {
      if (f.type === "number" || f.type === "integer") {
        let sum = 0;
        for (const r of filteredRows) {
          const v = r[f.name];
          const num = typeof v === "number" ? v : Number(v);
          if (Number.isFinite(num)) sum += num;
        }
        res[f.name] = sum;
      }
    }
    return res;
  }, [fields, filteredRows]);

  if (loading) return <div>Loading transactions...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Transactions</h1>
        <button
          type="button"
          onClick={clearFilters}
          style={{ background: "#e2e8f0", color: "#0f172a", padding: "8px 12px", borderRadius: 8, border: "none", cursor: "pointer" }}
        >
          Clear Filters
        </button>
        <button
          type="button"
          onClick={recalcAllFees}
          disabled={recalcLoading}
          style={{ background: recalcLoading ? "#94a3b8" : "#10b981", color: "white", padding: "8px 12px", borderRadius: 8, border: "none", cursor: recalcLoading ? "not-allowed" : "pointer" }}
          title="Recalculate transaction and external manager fees for all transactions"
        >
          {recalcLoading ? "Recalculating..." : "Recalculate Fees"}
        </button>
        {recalcMessage ? (
          <span style={{ color: "#0f766e", fontSize: 12 }}>
            {recalcMessage}
          </span>
        ) : null}
        <Link to="/transactions/performance-comparison" style={{ background: "#10b981", color: "white", padding: "8px 12px", borderRadius: 8, textDecoration: "none", marginRight: 8 }}>
          Performance Comparison
        </Link>
        <Link to="/transactions/new" style={{ background: "#0f172a", color: "white", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
          Add Transaction
        </Link>
      </div>

      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflowX: "auto", overflowY: "auto", marginTop: 12, maxHeight: "calc(100vh - 160px)" }}>
        <table style={{ width: "max-content", minWidth: "100%", borderCollapse: "collapse" }}>
          <thead style={{ background: "#f1f5f9", position: "sticky", top: 0, zIndex: 5 }}>
            <tr>
              <th style={{ textAlign: "left", padding: 12, whiteSpace: "nowrap", position: "sticky", top: 0, background: "#f1f5f9" }}>Actions</th>
              {fields.map((f) => (
                <th key={f.name} style={{ textAlign: "left", padding: 12, whiteSpace: "nowrap", position: "sticky", top: 0, background: "#f1f5f9" }}>
                  <button
                    type="button"
                    onClick={() => onHeaderClick(f.name)}
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      fontWeight: 600,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                      color: "#0f172a",
                    }}
                    title={`Sort by ${labelize(f.name)}`}
                  >
                    <span>{labelize(f.name)}</span>
                    <span style={{ opacity: 0.7 }}>
                      {sortBy === f.name ? (sortDir === "asc" ? "▲" : "▼") : "↕"}
                    </span>
                  </button>
                </th>
              ))}
            </tr>
            <tr>
              <th style={{ padding: 8, position: "sticky", top: 44, background: "#f1f5f9" }} />
              {fields.map((f) => (
                <th key={`${f.name}-filter`} style={{ textAlign: "left", padding: 8, whiteSpace: "nowrap", position: "sticky", top: 44, background: "#f1f5f9" }}>
                  {f.type === "date" ? (
                    <input
                      type="date"
                      value={filters[f.name] ?? ""}
                      onChange={(e) => onFilterChange(f.name, e.target.value)}
                      style={{ width: "100%", maxWidth: 180, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }}
                    />
                  ) : f.type === "integer" || f.type === "number" ? (
                    <input
                      type="text"
                      placeholder="e.g. =10, >5"
                      value={filters[f.name] ?? ""}
                      onChange={(e) => onFilterChange(f.name, e.target.value)}
                      style={{ width: "100%", maxWidth: 180, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }}
                    />
                  ) : (
                    <input
                      type="text"
                      placeholder={`Filter ${labelize(f.name)}`}
                      value={filters[f.name] ?? ""}
                      onChange={(e) => onFilterChange(f.name, e.target.value)}
                      style={{ width: "100%", maxWidth: 220, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }}
                    />
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((t, idx) => {
              const id = t.transaction_id ?? t.id;
              // Check if this transaction ID appears as rel_transaction_id in any other transaction
              const hasBeenDuplicated = sortedRows.some(other => other.rel_transaction_id === id);
              return (
                <tr key={id ?? JSON.stringify(t)} style={{ borderTop: "1px solid #e2e8f0", background: idx % 2 === 1 ? "#f8fafc" : "white" }}>
                  <td style={{ padding: 12, whiteSpace: "nowrap" }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <Link to={`/transactions/${id}/edit`} title="Edit" aria-label="Edit transaction">
                        <img src={editImg} alt="Edit" style={{ width: 20, height: 20 }} />
                      </Link>
                      {!hasBeenDuplicated && (
                        <Link to={`/transactions/${id}/duplicate`} title="Duplicate as VOO" aria-label="Duplicate transaction as VOO">
                          <span style={{ fontSize: 16, color: "#0f172a", textDecoration: "none" }}>⧉</span>
                        </Link>
                      )}
                      <Link to={`/transactions/${id}/delete`} title="Delete" aria-label="Delete transaction">
                        <img src={deleteImg} alt="Delete" style={{ width: 20, height: 20 }} />
                      </Link>
                    </div>
                  </td>
                  {fields.map((f) => (
                    <td key={f.name} style={{ padding: 12, whiteSpace: "nowrap" }}>
                      {renderCell(t[f.name], f)}
                    </td>
                  ))}
                </tr>
              );
            })}
            {sortedRows.length === 0 && (
              <tr>
                <td colSpan={fields.length + 1} style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                  No transactions found.
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr style={{ borderTop: "2px solid #e2e8f0", background: "#f8fafc" }}>
              <td style={{ padding: 12, whiteSpace: "nowrap", fontWeight: 700 }}>Totals ({filteredRows.length})</td>
              {fields.map((f) => (
                <td key={`total-${f.name}`} style={{ padding: 12, whiteSpace: "nowrap", fontWeight: 700 }}>
                  {f.type === "number" || f.type === "integer" ? renderCell(totals[f.name] ?? 0, f) : ""}
                </td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
