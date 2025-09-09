import React from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client.js";
import { getOrderedFields, renderCell, labelize } from "../../models/fields.js";

export default function PortfoliosList() {
  const [rows, setRows] = React.useState([]);
  const [fields, setFields] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        // Load fields and data
        const f = getOrderedFields("PortfolioDtl");
        // Move portfolio_id to end in the list view per requirement
        const ordered = [...f.filter(x => x.name !== "portfolio_id"), f.find(x => x.name === "portfolio_id")].filter(Boolean);
        if (alive) setFields(ordered);
        const [portfolios, users] = await Promise.all([
          api.listPortfolios(),
          api.listUsers(),
        ]);
        const userMap = new Map(users.map(u => [u.user_id, `${u.first_name} ${u.last_name}`.trim()]));
        const withUserName = portfolios.map(p => ({
          ...p,
          user_name: userMap.get(p.user_id) || `User ${p.user_id}`,
        }));
        if (alive) setRows(withUserName);
      } catch (e) {
        if (alive) setError("Failed to load portfolios.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => (alive = false);
  }, []);

  if (loading) return <div>Loading portfolios...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Portfolios</h1>
        <Link to="/portfolios/new" style={{ background: "#0f172a", color: "white", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
          Add Portfolio
        </Link>
      </div>

      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflow: "auto", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 720 }}>
          <thead style={{ background: "#f1f5f9" }}>
            <tr>
              {/* Replace user_id column with User Name and move Id to the end */}
              {fields.map((f) => (
                f.name === "user_id" ? (
                  <th key="user_name" style={{ textAlign: "left", padding: 12, whiteSpace: "nowrap" }}>
                    User Name
                  </th>
                ) : (
                  <th key={f.name} style={{ textAlign: "left", padding: 12, whiteSpace: "nowrap" }}>
                    {labelize(f.name)}
                  </th>
                )
              ))}
              <th style={{ textAlign: "left", padding: 12 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => {
              const id = p.portfolio_id ?? p.id;
              return (
                <tr key={id ?? JSON.stringify(p)} style={{ borderTop: "1px solid #e2e8f0" }}>
                  {fields.map((f) => (
                    f.name === "user_id" ? (
                      <td key="user_name" style={{ padding: 12 }}>
                        {p.user_name} ({p.user_id})
                      </td>
                    ) : (
                      <td key={f.name} style={{ padding: 12 }}>
                        {renderCell(p[f.name], f)}
                      </td>
                    )
                  ))}
                  <td style={{ padding: 12, display: "flex", gap: 8, whiteSpace: "nowrap" }}>
                    <Link to={`/portfolios/${id}/edit`}>Edit</Link>
                    <Link to={`/portfolios/${id}/delete`} style={{ color: "#b91c1c" }}>
                      Delete
                    </Link>
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={fields.length + 1} style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                  No portfolios found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}