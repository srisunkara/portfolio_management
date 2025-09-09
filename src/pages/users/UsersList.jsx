import React from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client.js";
import { getOrderedFields, renderCell, labelize } from "../../models/fields.js";

export default function UsersList() {
  const [rows, setRows] = React.useState([]);
  const [fields, setFields] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const f = getOrderedFields("UserDtl");
        if (alive) setFields(f);
        const data = await api.listUsers();
        if (alive) setRows(data);
      } catch (e) {
        if (alive) setError("Failed to load users.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => (alive = false);
  }, []);

  if (loading) return <div>Loading users...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Users</h1>
        <Link to="/users/new" style={{ background: "#0f172a", color: "white", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
          Add User
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
            {rows.map((u) => {
              const id = u.user_id ?? u.id;
              return (
                <tr key={id ?? JSON.stringify(u)} style={{ borderTop: "1px solid #e2e8f0" }}>
                  {fields.map((f) => (
                    <td key={f.name} style={{ padding: 12 }}>
                      {renderCell(u[f.name], f)}
                    </td>
                  ))}
                  <td style={{ padding: 12, display: "flex", gap: 8, whiteSpace: "nowrap" }}>
                    <Link to={`/users/${id}/edit`}>Edit</Link>
                    <Link to={`/users/${id}/delete`} style={{ color: "#b91c1c" }}>
                      Delete
                    </Link>
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={fields.length + 1} style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                  No users found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
