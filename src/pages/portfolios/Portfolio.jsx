import React from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client.js";
import { getOrderedFields, renderCell, labelize } from "../../models/fields.js";
import editImg from "../../images/edit.png";
import deleteImg from "../../images/delete.png";

export default function PortfoliosList() {
  const [rows, setRows] = React.useState([]);
  const [fields, setFields] = React.useState([]);
  const [filters, setFilters] = React.useState({});
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
        // Handle user name display column: allow filter by user_name even though fields include user_id
        if (f.name === "user_id") {
          const composite = `${row.user_name ?? ""} (${row.user_id ?? ""})`;
          return String(composite).toLowerCase().includes(String(fv).toLowerCase());
        }
        return String(rv ?? "").toLowerCase().includes(String(fv).toLowerCase());
      })
    );
  }, [rows, fields, filters]);

  if (loading) return <div>Loading portfolios...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Portfolios</h1>
        <button
          type="button"
          onClick={clearFilters}
          style={{ background: "#e2e8f0", color: "#0f172a", padding: "8px 12px", borderRadius: 8, border: "none", cursor: "pointer" }}
        >
          Clear Filters
        </button>
        <Link to="/portfolios/new" style={{ background: "#0f172a", color: "white", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
          Add Portfolio
        </Link>
      </div>

      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflow: "auto", marginTop: 12, maxHeight: "calc(100vh - 160px)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 720 }}>
          <thead style={{ background: "#f1f5f9" }}>
            <tr>
              <th style={{ textAlign: "left", padding: 12, whiteSpace: "nowrap" }}>Actions</th>
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
            </tr>
            <tr>
              <th style={{ padding: 8 }} />
              {fields.map((f) => (
                <th key={`${f.name}-filter`} style={{ textAlign: "left", padding: 8 }}>
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
                      placeholder={`Filter ${labelize(f.name === "user_id" ? "user_name" : f.name)}`}
                      value={filters[f.name] ?? ""}
                      onChange={(e) => onFilterChange(f.name, e.target.value)}
                      style={{ width: "100%", maxWidth: 220, padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }}
                    />
                  )}
                </th>
              ))}
              <th />
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((p, idx) => {
              const id = p.portfolio_id ?? p.id;
              return (
                <tr key={id ?? JSON.stringify(p)} style={{ borderTop: "1px solid #e2e8f0", background: idx % 2 === 1 ? "#f8fafc" : "white" }}>
                  <td style={{ padding: 12, whiteSpace: "nowrap" }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <Link to={`/portfolios/${id}/edit`} title="Edit" aria-label="Edit portfolio">
                        <img src={editImg} alt="Edit" style={{ width: 20, height: 20 }} />
                      </Link>
                      <Link to={`/portfolios/${id}/delete`} title="Delete" aria-label="Delete portfolio">
                        <img src={deleteImg} alt="Delete" style={{ width: 20, height: 20 }} />
                      </Link>
                    </div>
                  </td>
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
                </tr>
              );
            })}
            {filteredRows.length === 0 && (
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