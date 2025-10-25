import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { formFieldsForAction, labelize, defaultValueForType, coerceValue } from "../../models/fields.js";

export default function PortfolioForm({ mode }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = mode === "edit";

  const [fields, setFields] = React.useState([]);
  const [form, setForm] = React.useState({});
  const { user } = useAuth();
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const f = formFieldsForAction("PortfolioDtl", isEdit ? "edit" : "create");
        let initial = {};
        const data = isEdit ? await api.getPortfolio(id) : null;
        if (isEdit && data) {
          for (const field of f) {
            initial[field.name] = data?.[field.name] ?? defaultValueForType(field.type);
          }
        } else {
          for (const field of f) initial[field.name] = defaultValueForType(field.type);
          // Default open_date to local today, leave close_date blank
          const today = new Date();
          const yyyy = today.getFullYear();
          const mm = String(today.getMonth() + 1).padStart(2, "0");
          const dd = String(today.getDate()).padStart(2, "0");
          if (Object.prototype.hasOwnProperty.call(initial, "open_date")) {
            initial.open_date = `${yyyy}-${mm}-${dd}`;
          }
          if (Object.prototype.hasOwnProperty.call(initial, "close_date")) {
            initial.close_date = "";
          }
          // Force user_id to current user for creation
          const uid = user?.user_id || user?.id || user?.userId || null;
          if (uid != null && Object.prototype.hasOwnProperty.call(initial, "user_id")) {
            initial.user_id = uid;
          }
        }
        if (alive) {
          setFields(f);
          setForm(initial);
        }
      } catch (e) {
        if (alive) setError("Failed to load portfolio data.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => (alive = false);
  }, [id, isEdit]);

  const onChange = (name, value) => setForm((prev) => ({ ...prev, [name]: value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload = {};
      for (const f of fields) payload[f.name] = coerceValue(form[f.name], f);
      if (isEdit) {
        await api.updatePortfolio(id, payload);
      } else {
        await api.createPortfolio(payload);
      }
      navigate("/portfolios", { replace: true });
    } catch (e) {
      setError("Failed to save portfolio.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>{isEdit ? "Edit Portfolio" : "Add Portfolio"}</h1>
      <form onSubmit={onSubmit} style={{ background: "white", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", display: "grid", gap: 12, maxWidth: 720 }}>
        {fields.map((f) => (
          <FieldInput key={f.name} field={f} value={form[f.name]} onChange={onChange} isEdit={isEdit} currentUser={user} />
        ))}
        {error && <div style={{ color: "#b91c1c" }}>{error}</div>}
        <div style={{ display: "flex", gap: 8 }}>
          <button type="submit" disabled={saving} style={{ background: "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer", opacity: saving ? 0.7 : 1 }}>
            {saving ? "Saving..." : "Save"}
          </button>
          <button type="button" onClick={() => navigate(-1)} style={{ background: "#e2e8f0", color: "#0f172a", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer" }}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

function FieldInput({ field, value, onChange, isEdit = false, currentUser = null }) {
  const { name, type, required } = field;
  if (name === "user_id") {
    // Hide the user selector; show read-only info instead (for transparency on edit),
    // and always bind to the current user on create.
    const uid = currentUser?.user_id || currentUser?.id || currentUser?.userId || "";
    const fullName = `${currentUser?.first_name || currentUser?.firstName || ""} ${currentUser?.last_name || currentUser?.lastName || ""}`.trim();
    const display = fullName || (currentUser?.email || "");
    // Ensure form state reflects the enforced user_id
    if (!isEdit && uid && value !== uid) {
      // Note: onChange available here; update silently
      setTimeout(() => onChange(name, uid), 0);
    }
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>User</span>
        <input type="text" value={display ? `${display} (ID: ${uid})` : String(uid)} readOnly style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1", background: "#f8fafc" }} />
      </label>
    );
  }

  if (type === "boolean") {
    return (
      <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input type="checkbox" checked={!!value} onChange={(e) => onChange(name, e.target.checked)} />
        <span>{labelize(name)}{required ? " *" : ""}</span>
      </label>
    );
  }
  if (type === "integer" || type === "number") {
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>{labelize(name)}{required ? " *" : ""}</span>
        <input type="number" value={value ?? ""} onChange={(e) => onChange(name, e.target.value === "" ? "" : Number(e.target.value))} step={type === "integer" ? 1 : "any"} required={!!required} style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
      </label>
    );
  }
  if (type === "date") {
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>{labelize(name)}{required ? " *" : ""}</span>
        <input type="date" value={value ?? ""} onChange={(e) => onChange(name, e.target.value)} required={!!required} style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
      </label>
    );
  }
  return (
    <label style={{ display: "grid", gap: 6 }}>
      <span>{labelize(name)}{required ? " *" : ""}</span>
      <input type="text" value={value ?? ""} onChange={(e) => onChange(name, e.target.value)} required={!!required} placeholder={name} style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
    </label>
  );
}
