import React from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client.js";

export default function SecuritiesImport() {
  const [tickersInput, setTickersInput] = React.useState("");
  const [importing, setImporting] = React.useState(false);
  const [importError, setImportError] = React.useState("");
  const [importResults, setImportResults] = React.useState([]);

  async function importByTickers(e) {
    e.preventDefault();
    setImportError("");
    const tokens = (tickersInput || "")
      .split(/[\s,;\n]+/)
      .map((t) => t.trim().toUpperCase())
      .filter((t) => !!t);
    if (tokens.length === 0) {
      setImportError("Please enter at least one ticker.");
      return;
    }
    setImporting(true);
    try {
      const res = await api.saveCompanyDataFromTickers(tokens);
      setImportResults(Array.isArray(res) ? res : []);
    } catch (err) {
      setImportError(err?.message || "Failed to import from tickers.");
    } finally {
      setImporting(false);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Import Securities by Tickers</h1>
        <Link to="/securities" style={{ background: "#e2e8f0", color: "#0f172a", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
          Back to Securities
        </Link>
      </div>

      <div style={{ marginTop: 12, padding: 12, background: "#ffffff", borderRadius: 12, boxShadow: "0 1px 6px rgba(0,0,0,0.06)" }}>
        <form onSubmit={importByTickers} style={{ display: "flex", gap: 12, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 320 }}>
            <label style={{ display: "block", marginBottom: 6, fontWeight: 600 }}>Add by Tickers (Yahoo)</label>
            <textarea
              rows={6}
              placeholder="Enter tickers separated by comma, space, or newline. e.g. VOO, AAPL, MSFT"
              value={tickersInput}
              onChange={(e) => setTickersInput(e.target.value)}
              style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #cbd5e1", fontFamily: "inherit" }}
            />
            <div style={{ color: "#64748b", fontSize: 12, marginTop: 4 }}>We will fetch company data and create/update securities.</div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button type="submit" disabled={importing} style={{ background: "#0f172a", color: "#fff", padding: "10px 14px", borderRadius: 8, border: "none", cursor: "pointer" }}>
              {importing ? "Importing..." : "Import"}
            </button>
          </div>
        </form>
        {importError && <div style={{ color: "#b91c1c", marginTop: 8 }}>{importError}</div>}
        {importResults && importResults.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Imported {importResults.length} securities:</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {importResults.map((s) => (
                <span key={s.security_id || s.ticker} style={{ background: "#e2e8f0", color: "#0f172a", padding: "6px 10px", borderRadius: 999 }}>
                  {(s.ticker || "").toUpperCase()} — {s.name || s.company_name || "Unnamed"}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {importResults && importResults.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <Link to="/securities" style={{ background: "#0f172a", color: "white", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
            View in Securities List
          </Link>
        </div>
      )}
    </div>
  );
}
