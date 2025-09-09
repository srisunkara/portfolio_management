import React from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client.js";
import { getOrderedFields, renderCell, labelize } from "../../models/fields.js";

export default function SecuritiesList() {
  const [rows, setRows] = React.useState([]);
  const [fields, setFields] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        // Use SecurityDtl’s ordered fields
        const f = getOrderedFields("SecurityDtl");
        if (alive) setFields(f);

        const data = await api.listSecurities();
        if (alive) setRows(data);
      } catch (e) {
        if (alive) setError("Failed to load securities.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => (alive = false);
  }, []);

  if (loading) return <div>Loading securities...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Securities</h1>
        <Link to="/securities/new" style={{ background: "#0f172a", color: "white", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
          Add Security
        </Link>
      </div>

      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflow: "auto", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 720 }}>
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
            {rows.map((s) => {
              const id = s.security_id ?? s.id ?? s.ID;
              return (
                <tr key={id ?? JSON.stringify(s)} style={{ borderTop: "1px solid #e2e8f0" }}>
                  {fields.map((f) => (
                    <td key={f.name} style={{ padding: 12 }}>
                      {renderCell(s[f.name], f)}
                    </td>
                  ))}
                  <td style={{ padding: 12, display: "flex", gap: 8, whiteSpace: "nowrap" }}>
                    <Link to={`/securities/${id}/edit`}>Edit</Link>
                    <Link to={`/securities/${id}/delete`} style={{ color: "#b91c1c" }}>
                      Delete
                    </Link>
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={fields.length + 1} style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                  No securities found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}