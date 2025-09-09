import React from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client.js";
import { getOrderedFields, renderCell, labelize, modelFieldDefs } from "../../models/fields.js";

export default function TransactionsList() {
  const [rows, setRows] = React.useState([]);
  const [fields, setFields] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const f = getOrderedFields("TransactionFullView");
        if (alive) setFields(f);
        const txns = await api.listTransactionsFull();
        if (alive) setRows(txns);
      } catch (e) {
        if (alive) setError("Failed to load transactions.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => (alive = false);
  }, []);

  if (loading) return <div>Loading transactions...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Transactions</h1>
        <Link to="/transactions/new" style={{ background: "#0f172a", color: "white", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
          Add Transaction
        </Link>
      </div>

      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflow: "auto", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 960 }}>
          <thead style={{ background: "#f1f5f9" }}>
            <tr>
              {fields.map((f) => (
                <th key={f.name} style={{ textAlign: "left", padding: 12, whiteSpace: "nowrap" }}>
                  {labelize(f.name)}
                </th>
              ))}
              <th style={{ textAlign: "left", padding: 12 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => {
              const id = t.transaction_id ?? t.id;
              return (
                <tr key={id ?? JSON.stringify(t)} style={{ borderTop: "1px solid #e2e8f0" }}>
                  {fields.map((f) => (
                    <td key={f.name} style={{ padding: 12 }}>
                      {renderCell(t[f.name], f)}
                    </td>
                  ))}
                  <td style={{ padding: 12, display: "flex", gap: 8, whiteSpace: "nowrap" }}>
                    <Link to={`/transactions/${id}/edit`}>Edit</Link>
                    <Link to={`/transactions/${id}/delete`} style={{ color: "#b91c1c" }}>
                      Delete
                    </Link>
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={fields.length + 1} style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                  No transactions found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
