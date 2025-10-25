import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { formFieldsForAction, labelize, defaultValueForType, coerceValue } from "../../models/fields.js";

export default function TransactionForm({ mode }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = mode === "edit";
  const { user } = useAuth();

  const [fields, setFields] = React.useState([]);
  const [form, setForm] = React.useState({});
  const [portfolios, setPortfolios] = React.useState([]);
  const [securities, setSecurities] = React.useState([]);
  const [platforms, setPlatforms] = React.useState([]);
  const [txnTypes, setTxnTypes] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const f = formFieldsForAction("TransactionDtl", isEdit ? "edit" : "create");
        let initial = {};
        const [formData, data] = await Promise.all([
          api.getTransactionFormData(),
          isEdit ? api.getTransaction(id) : Promise.resolve(null),
        ]);
        if (isEdit && data) {
          for (const field of f) {
            initial[field.name] = data?.[field.name] ?? defaultValueForType(field.type);
          }
        } else {
          for (const field of f) initial[field.name] = defaultValueForType(field.type);
          // Default transaction_type to 'B' (Buy)
          if (Object.prototype.hasOwnProperty.call(initial, "transaction_type")) {
            initial.transaction_type = "B";
          }
          // Default all fees to 0 for new transactions
          const feeFields = [
            "transaction_fee", "transaction_fee_percent",
            "management_fee", "management_fee_percent", 
            "external_manager_fee", "external_manager_fee_percent",
            "carry_fee", "carry_fee_percent"
          ];
          for (const feeField of feeFields) {
            if (Object.prototype.hasOwnProperty.call(initial, feeField)) {
              initial[feeField] = 0;
            }
          }
        }
        if (alive) {
          setFields(f);
          const uid = user?.user_id || user?.id || user?.userId;
          const allPortfolios = formData?.portfolios || [];
          const visiblePortfolios = (!isEdit && uid != null)
            ? allPortfolios.filter(p => p && p.user_id === uid)
            : allPortfolios;
          setPortfolios(visiblePortfolios);
          setSecurities(formData?.securities || []);
          setPlatforms(formData?.external_platforms || []);
          setTxnTypes(formData?.transaction_types || []);
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

  const onChange = (name, value) => {
    setForm((prev) => {
      const next = { ...prev, [name]: value };
      // Auto-calc Total Inv Amt when qty or price changes
      if (name === "transaction_qty" || name === "transaction_price") {
        const qty = Number(next.transaction_qty);
        const price = Number(next.transaction_price);
        if (Number.isFinite(qty) && Number.isFinite(price)) {
          const total = Math.round(qty * price * 100) / 100;
          next.total_inv_amt = total;
        } else {
          next.total_inv_amt = "";
        }
      }
      return next;
    });
  };

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
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>{isEdit ? "Edit Transaction" : "Add Transaction"}</h1>
      </div>
      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflowY: "auto", overflowX: "auto", marginTop: 12, maxHeight: "calc(100vh - 160px)", padding: 16 }}>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 12, maxWidth: 1080, gridTemplateColumns: "repeat(2, minmax(280px, 1fr))" }}>
        {fields.map((f) => (
          <FieldInput key={f.name} field={f} value={form[f.name]} onChange={onChange} portfolios={portfolios} securities={securities} platforms={platforms} txnTypes={txnTypes} />
        ))}
        {error && <div style={{ color: "#b91c1c", gridColumn: "1 / -1" }}>{error}</div>}
        <div style={{ display: "flex", gap: 8, gridColumn: "1 / -1" }}>
          <button type="submit" disabled={saving} style={{ background: "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer", opacity: saving ? 0.7 : 1 }}>
            {saving ? "Saving..." : "Save"}
          </button>
          <button type="button" onClick={() => navigate(-1)} style={{ background: "#e2e8f0", color: "#0f172a", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer" }}>
            Cancel
          </button>
        </div>
      </form>
      </div>
    </div>
  );
}

function FieldInput({ field, value, onChange, portfolios = [], securities = [], platforms = [], txnTypes = [] }) {
  const { name, type, required } = field;

  // Inline searchable dropdown state for security_id (mirrors Add Security Price page behavior)
  const [secSearchTerm, setSecSearchTerm] = React.useState("");
  const [secIsOpen, setSecIsOpen] = React.useState(false);
  const [secSelected, setSecSelected] = React.useState(null);
  const secDropdownRef = React.useRef(null);

  // Sync selected security with incoming value
  React.useEffect(() => {
    const sel = securities.find((s) => s.security_id === value);
    setSecSelected(sel || null);
    if (sel) {
      setSecSearchTerm(sel.ticker || sel.name || "");
    } else {
      setSecSearchTerm("");
    }
  }, [value, securities]);

  // Filter securities by search term
  const secFiltered = React.useMemo(() => {
    if (!secSearchTerm) return securities;
    const term = secSearchTerm.toLowerCase();
    return securities.filter((s) =>
      (s.ticker && s.ticker.toLowerCase().includes(term)) ||
      (s.name && s.name.toLowerCase().includes(term)) ||
      String(s.security_id ?? "").includes(term)
    );
  }, [securities, secSearchTerm]);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    function handleClickOutside(e) {
      if (secDropdownRef.current && !secDropdownRef.current.contains(e.target)) {
        setSecIsOpen(false);
        // Reset search box to selected display if exists
        if (secSelected) {
          setSecSearchTerm(secSelected.ticker || secSelected.name || "");
        } else {
          setSecSearchTerm("");
        }
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [secSelected]);

  const onSecInputChange = (e) => {
    setSecSearchTerm(e.target.value);
    setSecIsOpen(true);
  };
  const onSecInputFocus = () => {
    setSecIsOpen(true);
    setSecSearchTerm("");
  };
  const onSecSelect = (s) => {
    setSecSelected(s);
    setSecSearchTerm(s.ticker || s.name || "");
    setSecIsOpen(false);
    onChange(name, s.security_id);
  };
  const onSecClear = () => {
    setSecSelected(null);
    setSecSearchTerm("");
    setSecIsOpen(false);
    onChange(name, "");
  };

  const secDisplay = secSelected
    ? `${secSelected.ticker || secSelected.name} (${secSelected.security_id})${secSelected.name && secSelected.ticker ? ` – ${secSelected.name}` : ""}`
    : "";

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
    // Searchable like Add Security Price page: inline input with dropdown list
    return (
      <div ref={secDropdownRef} style={{ position: "relative", display: "grid", gap: 6 }}>
        <span>Security{required ? " *" : ""}</span>
        <div style={{ position: "relative" }}>
          <input
            type="text"
            value={secIsOpen ? secSearchTerm : secDisplay}
            onChange={onSecInputChange}
            onFocus={onSecInputFocus}
            placeholder="Search for a security..."
            required={!!required}
            style={{
              padding: 10,
              paddingRight: secSelected ? 35 : 10,
              borderRadius: 8,
              border: "1px solid #cbd5e1",
              width: "100%",
              boxSizing: "border-box"
            }}
          />
          {secSelected && (
            <button
              type="button"
              onClick={onSecClear}
              style={{
                position: "absolute",
                right: 8,
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: 16,
                color: "#64748b",
                padding: 2
              }}
              title="Clear selection"
              aria-label="Clear selection"
            >
              ×
            </button>
          )}
        </div>

        {secIsOpen && (
          <div
            style={{
              position: "absolute",
              zIndex: 10,
              top: "100%",
              left: 0,
              right: 0,
              background: "white",
              border: "1px solid #e2e8f0",
              borderRadius: 8,
              marginTop: 4,
              maxHeight: 240,
              overflowY: "auto",
              boxShadow: "0 8px 24px rgba(0,0,0,0.08)"
            }}
            role="listbox"
          >
            {secFiltered.length === 0 && (
              <div style={{ padding: 10, color: "#64748b" }}>No matches</div>
            )}
            {secFiltered.map((s) => (
              <div
                key={s.security_id}
                onClick={() => onSecSelect(s)}
                role="option"
                aria-selected={secSelected?.security_id === s.security_id}
                style={{
                  padding: "8px 10px",
                  cursor: "pointer",
                  backgroundColor: secSelected?.security_id === s.security_id ? "#f1f5f9" : "white"
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f1f5f9")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = secSelected?.security_id === s.security_id ? "#f1f5f9" : "white")}
              >
                {(s.ticker || s.name)} ({s.security_id})
                {s.name && s.ticker && (
                  <div style={{ fontSize: 12, color: "#64748b" }}>{s.name}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
  if (name === "transaction_type") {
    // Select with options (label shown, code stored)
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>Transaction Type{required ? " *" : ""}</span>
        <select value={value ?? ""} onChange={(e) => onChange(name, e.target.value)} required={!!required} style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}>
          {(txnTypes && txnTypes.length > 0 ? txnTypes : [{ code: "B", label: "Buy" }, { code: "S", label: "Sell" }]).map((t) => (
            <option key={t.code} value={t.code}>{t.label}</option>
          ))}
        </select>
      </label>
    );
  }
  if (name === "external_platform_id") {
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>Trading Platform</span>
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

  if (name === "total_inv_amt") {
    // Computed from quantity x price; show as read-only
    const displayVal = value ?? "";
    return (
      <label style={{ display: "grid", gap: 6 }}>
        <span>Total Inv Amt</span>
        <input
          type="number"
          value={displayVal}
          readOnly
          inputMode="decimal"
          step="any"
          style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1", background: "#f8fafc" }}
        />
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
          onWheel={(e) => { e.preventDefault(); e.stopPropagation(); /* prevent accidental wheel changes */ }}
          inputMode={type === "integer" ? "numeric" : "decimal"}
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
