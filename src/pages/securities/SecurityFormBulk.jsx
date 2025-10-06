import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client.js";

// Bulk Add Securities form (table-style)
export default function SecurityFormBulk() {
  const navigate = useNavigate();
  const [rows, setRows] = React.useState(() => [emptyRow(), emptyRow(), emptyRow()]);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");
  const [result, setResult] = React.useState(null);

  function emptyRow() {
    return { ticker: "", name: "", company_name: "", security_currency: "USD", is_private: false };
  }

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);
  const removeRow = (idx) => setRows((prev) => prev.filter((_, i) => i !== idx));
  const updateCell = (idx, field, value) =>
    setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, [field]: value } : r)));
  const clearAll = () => setRows([emptyRow()]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setSaving(true);
    try {
      // Prepare payload: keep only rows with required fields
      const payload = rows
        .map((r) => ({
          ticker: (r.ticker || "").trim(),
          name: (r.name || "").trim(),
          company_name: (r.company_name || "").trim(),
          security_currency: ((r.security_currency || "USD").trim() || "USD").toUpperCase(),
          is_private: !!r.is_private,
        }))
        .filter((r) => r.ticker && r.name && r.company_name);

      if (payload.length === 0) {
        setError("Please enter at least one complete row (ticker, name, company_name).");
        return;
      }

      const res = await api.createSecuritiesBulkUnique(payload);
      setResult(res);
    } catch (e) {
      setError(e?.message || "Failed to save securities.");
    } finally {
      setSaving(false);
    }
  };

  const addedCount = result?.added ? result.added.length : 0;
  const skippedCount = result?.skipped ? result.skipped.length : 0;

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Add Securities (Bulk)</h1>
      <form onSubmit={onSubmit} style={{ background: "white", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", display: "grid", gap: 12 }}>
        <div style={{ overflow: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 900 }}>
            <thead style={{ background: "#f1f5f9" }}>
              <tr>
                <th style={{ textAlign: "left", padding: 8 }}>Ticker</th>
                <th style={{ textAlign: "left", padding: 8 }}>Name</th>
                <th style={{ textAlign: "left", padding: 8 }}>Company Name</th>
                <th style={{ textAlign: "left", padding: 8 }}>Currency</th>
                <th style={{ textAlign: "left", padding: 8 }}>Private?</th>
                <th style={{ textAlign: "left", padding: 8 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, idx) => (
                <tr key={idx} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={{ padding: 6 }}>
                    <input
                      type="text"
                      value={r.ticker}
                      onChange={(e) => updateCell(idx, "ticker", e.target.value)}
                      placeholder="e.g. AAPL"
                      style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}
                    />
                  </td>
                  <td style={{ padding: 6 }}>
                    <input
                      type="text"
                      value={r.name}
                      onChange={(e) => updateCell(idx, "name", e.target.value)}
                      placeholder="Security Name"
                      style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}
                    />
                  </td>
                  <td style={{ padding: 6 }}>
                    <input
                      type="text"
                      value={r.company_name}
                      onChange={(e) => updateCell(idx, "company_name", e.target.value)}
                      placeholder="Company Name"
                      style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}
                    />
                  </td>
                  <td style={{ padding: 6 }}>
                    <input
                      type="text"
                      value={r.security_currency}
                      onChange={(e) => updateCell(idx, "security_currency", e.target.value.toUpperCase())}
                      placeholder="USD"
                      style={{ width: 120, padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}
                    />
                  </td>
                  <td style={{ padding: 6 }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <input
                        type="checkbox"
                        checked={!!r.is_private}
                        onChange={(e) => updateCell(idx, "is_private", e.target.checked)}
                      />
                      <span>Private</span>
                    </label>
                  </td>
                  <td style={{ padding: 6 }}>
                    <button type="button" onClick={() => removeRow(idx)} style={{ background: "#ef4444", color: "white", border: "none", padding: "6px 10px", borderRadius: 6, cursor: "pointer" }}>Remove</button>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: 12, textAlign: "center", color: "#64748b" }}>No rows. Click Add Row.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <button type="button" onClick={addRow} style={{ background: "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer" }}>Add Row</button>
          <button type="button" onClick={clearAll} style={{ background: "#e2e8f0", color: "#0f172a", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer" }}>Clear</button>
          <button type="submit" disabled={saving} style={{ background: saving ? "#94a3b8" : "#10b981", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: saving ? "not-allowed" : "pointer" }}>
            {saving ? "Saving..." : "Save All"}
          </button>
          <Link to="/securities" style={{ background: "#e2e8f0", color: "#0f172a", padding: "10px 12px", borderRadius: 8, textDecoration: "none" }}>Back to List</Link>
        </div>
        {error && <div style={{ color: "#b91c1c" }}>{error}</div>}
        {result && (
          <div style={{ background: "#f1f5f9", padding: 12, borderRadius: 8 }}>
            <div><strong>Added:</strong> {addedCount}</div>
            <div><strong>Skipped:</strong> {skippedCount}</div>
            {Array.isArray(result.skipped) && result.skipped.length > 0 && (
              <details style={{ marginTop: 8 }}>
                <summary>Skipped Details ({result.skipped.length})</summary>
                <ul>
                  {result.skipped.map((s, i) => (
                    <li key={i} style={{ color: "#b91c1c" }}>
                      {typeof s === "string" ? s : `${s.reason}: ${JSON.stringify(s.input)}`}
                    </li>
                  ))}
                </ul>
              </details>
            )}
            {Array.isArray(result.added) && result.added.length > 0 && (
              <details style={{ marginTop: 8 }}>
                <summary>Added Details ({result.added.length})</summary>
                <ul>
                  {result.added.map((a, i) => (
                    <li key={i}>{`${a.ticker} — ${a.name}`}</li>
                  ))}
                </ul>
              </details>
            )}
            <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
              <button type="button" onClick={() => navigate("/securities", { replace: true })} style={{ background: "#0f172a", color: "white", border: "none", padding: "8px 12px", borderRadius: 8, cursor: "pointer" }}>Go to List</button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
