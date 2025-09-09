import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client.js";
import { formFieldsForAction, labelize, defaultValueForType, coerceValue } from "../../models/fields.js";

export default function TransactionForm({ mode }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = mode === "edit";

  const [fields, setFields] = React.useState([]);
  const [form, setForm] = React.useState({});
  const [portfolios, setPortfolios] = React.useState([]);
  const [securities, setSecurities] = React.useState([]);
  const [platforms, setPlatforms] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const f = formFieldsForAction("TransactionDtl", isEdit ? "edit" : "create");
        let initial = {};
        const [pfRes, secRes, tpRes, data] = await Promise.all([
          api.listPortfolios(),
          api.listSecurities(),
          api.listExternalPlatforms(),
          isEdit ? api.getTransaction(id) : Promise.resolve(null),
        ]);
        if (isEdit && data) {
          for (const field of f) {
            initial[field.name] = data?.[field.name] ?? defaultValueForType(field.type);
          }
        } else {
          for (const field of f) initial[field.name] = defaultValueForType(field.type);
        }
        if (alive) {
          setFields(f);
          setPortfolios(pfRes || []);
          setSecurities(secRes || []);
          setPlatforms(tpRes || []);
          setForm(initial);
        }
      } catch (e) {
        if (alive) setError("Failed to load transaction data.");
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
        await api.updateTransaction(id, payload);
      } else {
        await api.createTransaction(payload);
      }
      navigate("/transactions", { replace: true });
    } catch (e) {
      setError("Failed to save transaction.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>{isEdit ? "Edit Transaction" : "Add Transaction"}</h1>
      <form onSubmit={onSubmit} style={{ background: "white", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", display: "grid", gap: 12, maxWidth: 960 }}>
        {fields.map((f) => (
          <FieldInput key={f.name} field={f} value={form[f.name]} onChange={onChange} portfolios={portfolios} securities={securities} platforms={platforms} />
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

function FieldInput({ field, value, onChange, portfolios = [], securities = [], platforms = [] }) {
  const { name, type, required } = field;

  if (name === "portfolio_id") {
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>Portfolio</span>
        <select value={value ?? ""} onChange={(e) => onChange(name, e.target.value === "" ? "" : Number(e.target.value))} required={!!required} style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}>
          <option value="">Select a portfolio…</option>
          {portfolios.map((p) => (
            <option key={p.portfolio_id} value={p.portfolio_id}>
              {p.name} ({p.portfolio_id})
            </option>
          ))}
        </select>
      </label>
    );
  }
  if (name === "security_id") {
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>Security</span>
        <select value={value ?? ""} onChange={(e) => onChange(name, e.target.value === "" ? "" : Number(e.target.value))} required={!!required} style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}>
          <option value="">Select a security…</option>
          {securities.map((s) => (
            <option key={s.security_id} value={s.security_id}>
              {(s.ticker || s.name)} ({s.security_id})
            </option>
          ))}
        </select>
      </label>
    );
  }
  if (name === "external_platform_id") {
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>External Platform</span>
        <select value={value ?? ""} onChange={(e) => onChange(name, e.target.value === "" ? "" : Number(e.target.value))} required={!!required} style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}>
          <option value="">Select a platform…</option>
          {platforms.map((ep) => (
            <option key={ep.external_platform_id} value={ep.external_platform_id}>
              {ep.name} ({ep.external_platform_id})
            </option>
          ))}
        </select>
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
        <input
          type="number"
          value={value ?? ""}
          onChange={(e) => onChange(name, e.target.value === "" ? "" : Number(e.target.value))}
          step={type === "integer" ? 1 : "any"}
          required={!!required}
          style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
        />
      </label>
    );
  }

  if (type === "date") {
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>{labelize(name)}{required ? " *" : ""}</span>
        <input
          type="date"
          value={value ?? ""}
          onChange={(e) => onChange(name, e.target.value)}
          required={!!required}
          style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
        />
      </label>
    );
  }

  return (
    <label style={{ display: "grid", gap: 6 }}>
      <span>{labelize(name)}{required ? " *" : ""}</span>
      <input
        type="text"
        value={value ?? ""}
        onChange={(e) => onChange(name, e.target.value)}
        required={!!required}
        placeholder={name}
        style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
      />
    </label>
  );
}
