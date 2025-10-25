import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { formFieldsForAction, labelize, defaultValueForType, coerceValue } from "../../models/fields.js";

export default function TransactionDuplicate() {
  const navigate = useNavigate();
  const { id } = useParams();
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
  const [originalTransaction, setOriginalTransaction] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const f = formFieldsForAction("TransactionDtl", "create");
        const [formData, originalTxn] = await Promise.all([
          api.getTransactionFormData(),
          api.getTransaction(id),
        ]);

        if (!originalTxn) {
          throw new Error("Original transaction not found");
        }

        setOriginalTransaction(originalTxn);

        // Find VOO security
        const vooSecurity = formData?.securities?.find(s => s.ticker === "VOO");
        if (!vooSecurity) {
          throw new Error("VOO security not found in database");
        }

        // Pick a default portfolio from the current user's portfolios
        const uid = user?.user_id || user?.id || user?.userId;
        const allPortfolios = formData?.portfolios || [];
        const userPortfolios = uid != null ? allPortfolios.filter(p => p && p.user_id === uid) : allPortfolios;
        setPortfolios(userPortfolios);
        const defaultPortfolio = userPortfolios?.[0];
        if (!defaultPortfolio) {
          throw new Error("No portfolios available for the current user");
        }

        // Initialize form with original transaction data but override key fields
        let initial = {};
        for (const field of f) {
          if (field.name === "security_id") {
            initial[field.name] = vooSecurity.security_id;
          } else if (field.name === "portfolio_id") {
            initial[field.name] = defaultPortfolio.portfolio_id;
          } else if (field.name === "transaction_qty") {
            // Will be calculated based on price and total amount
            initial[field.name] = "";
          } else if (field.name === "transaction_price") {
            // Will be fetched from database based on transaction date
            initial[field.name] = "";
          } else if (field.name === "rel_transaction_id") {
            // Set to original transaction ID to link the duplicate
            initial[field.name] = originalTxn.transaction_id;
          } else if (field.name === "transaction_fee" || 
                     field.name === "transaction_fee_percent" ||
                     field.name === "management_fee" ||
                     field.name === "management_fee_percent" ||
                     field.name === "external_manager_fee" ||
                     field.name === "external_manager_fee_percent" ||
                     field.name === "carry_fee" ||
                     field.name === "carry_fee_percent") {
            // Default all fees and commissions to 0
            initial[field.name] = 0;
          } else {
            // Copy from original transaction
            initial[field.name] = originalTxn?.[field.name] ?? defaultValueForType(field.type);
          }
        }

        // Fetch VOO price for the transaction date
        try {
          const pricesForDate = await api.listSecurityPrices(originalTxn.transaction_date);
          const vooPrice = pricesForDate.find(p => p.security_id === vooSecurity.security_id);
          
          if (vooPrice && originalTxn.total_inv_amt) {
            initial.transaction_price = vooPrice.price;
            // Calculate quantity: total_inv_amt / price
            initial.transaction_qty = Math.round((originalTxn.total_inv_amt / vooPrice.price) * 100) / 100;
          }
        } catch (e) {
          console.warn("Could not fetch VOO price for date:", originalTxn.transaction_date, e);
        }

        if (alive) {
          setFields(f);
          setPortfolios(formData?.portfolios || []);
          setSecurities(formData?.securities || []);
          setPlatforms(formData?.external_platforms || []);
          setTxnTypes(formData?.transaction_types || []);
          setForm(initial);
        }
      } catch (e) {
        if (alive) setError(e.message || "Failed to load transaction data.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => (alive = false);
  }, [id]);

  const onChange = (name, value) => setForm((prev) => ({ ...prev, [name]: value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload = {};
      for (const f of fields) payload[f.name] = coerceValue(form[f.name], f);
      await api.createTransaction(payload);
      navigate("/transactions", { replace: true });
    } catch (e) {
      setError("Failed to create duplicate transaction.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>
          Duplicate Transaction as VOO
        </h1>
      </div>
      
      {originalTransaction && (
        <div style={{ background: "#f8fafc", padding: 12, borderRadius: 8, marginTop: 12, fontSize: 14 }}>
          <strong>Original Transaction:</strong> {originalTransaction.transaction_date} - ${originalTransaction.total_inv_amt} 
          {originalTransaction.security_ticker && ` in ${originalTransaction.security_ticker}`}
        </div>
      )}

      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflowY: "auto", overflowX: "auto", marginTop: 12, maxHeight: "calc(100vh - 200px)", padding: 16 }}>
        <form onSubmit={onSubmit} style={{ display: "grid", gap: 12, maxWidth: 960 }}>
          {fields.map((f) => (
            <FieldInput 
              key={f.name} 
              field={f} 
              value={form[f.name]} 
              onChange={onChange} 
              portfolios={portfolios} 
              securities={securities} 
              platforms={platforms} 
              txnTypes={txnTypes} 
            />
          ))}
          {error && <div style={{ color: "#b91c1c" }}>{error}</div>}
          <div style={{ display: "flex", gap: 8 }}>
            <button type="submit" disabled={saving} style={{ background: "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer", opacity: saving ? 0.7 : 1 }}>
              {saving ? "Creating..." : "Create Duplicate Transaction"}
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

// Reuse the same FieldInput component from TransactionForm
function FieldInput({ field, value, onChange, portfolios = [], securities = [], platforms = [], txnTypes = [] }) {
  const { name, type, required } = field;

  if (name === "portfolio_id") {
    return (
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>Portfolio{required ? " *" : ""}</span>
        <select
          value={value || ""}
          onChange={(e) => onChange(name, e.target.value)}
          style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1" }}
        >
          <option value="">-- Select Portfolio --</option>
          {portfolios.map((p) => (
            <option key={p.portfolio_id} value={p.portfolio_id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (name === "security_id") {
    return (
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>Security{required ? " *" : ""}</span>
        <select
          value={value || ""}
          onChange={(e) => onChange(name, e.target.value)}
          style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1" }}
        >
          <option value="">-- Select Security --</option>
          {securities.map((s) => (
            <option key={s.security_id} value={s.security_id}>
              {s.ticker} - {s.name}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (name === "external_platform_id") {
    return (
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>External Platform{required ? " *" : ""}</span>
        <select
          value={value || ""}
          onChange={(e) => onChange(name, e.target.value)}
          style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1" }}
        >
          <option value="">-- Select Platform --</option>
          {platforms.map((p) => (
            <option key={p.external_platform_id} value={p.external_platform_id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (name === "transaction_type") {
    return (
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>Transaction Type{required ? " *" : ""}</span>
        <select
          value={value || ""}
          onChange={(e) => onChange(name, e.target.value)}
          style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1" }}
        >
          <option value="">-- Select Type --</option>
          {txnTypes.map((t) => (
            <option key={t.code} value={t.code}>
              {t.label}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (name === "rel_transaction_id") {
    return (
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span>{labelize(name)}{required ? " *" : ""}</span>
        <input
          type={type === "number" || type === "integer" ? "number" : "text"}
          value={value || ""}
          readOnly
          style={{ 
            padding: 8, 
            borderRadius: 6, 
            border: "1px solid #cbd5e1", 
            backgroundColor: "#f8fafc", 
            color: "#64748b",
            cursor: "not-allowed"
          }}
        />
      </label>
    );
  }

  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span>{labelize(name)}{required ? " *" : ""}</span>
      <input
        type={type === "date" ? "date" : type === "number" || type === "integer" ? "number" : "text"}
        step={type === "number" ? "0.01" : undefined}
        value={value || ""}
        onChange={(e) => onChange(name, e.target.value)}
        style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1" }}
      />
    </label>
  );
}