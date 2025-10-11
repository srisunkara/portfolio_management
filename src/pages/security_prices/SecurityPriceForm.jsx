import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client.js";

export default function SecurityPriceForm() {
  const navigate = useNavigate();
  const { id } = useParams();

  const [securities, setSecurities] = React.useState([]);
  const [platforms, setPlatforms] = React.useState([]);
  const [form, setForm] = React.useState({
    security_id: "",
    price_source_id: "",
    price_date: "",
    price: "",
    market_cap: "",
    addl_notes: "",
    price_currency: "",
  });
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");

  const isEdit = !!id;

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        if (isEdit) {
          const [price, secs, plats] = await Promise.all([
            api.getSecurityPrice(id),
            api.listSecurities(),
            api.listExternalPlatforms(),
          ]);
          if (!alive) return;
          setSecurities(secs || []);
          setPlatforms(plats || []);
          setForm({
            security_id: price.security_id ?? "",
            price_source_id: price.price_source_id ?? "",
            price_date: typeof price.price_date === "string" ? price.price_date : new Date(price.price_date).toISOString().slice(0, 10),
            price: price.price ?? "",
            market_cap: price.market_cap ?? "",
            addl_notes: price.addl_notes ?? "",
            price_currency: price.price_currency ?? "USD",
          });
        } else {
          const [secs, plats] = await Promise.all([
            api.listSecurities(),
            api.listExternalPlatforms(),
          ]);
          if (!alive) return;
          setSecurities(secs || []);
          setPlatforms(plats || []);
          setForm((prev) => ({
            ...prev,
            price_currency: "USD",
          }));
        }
      } catch (e) {
        if (alive) setError("Failed to load price.");
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
    
    // Validate required fields
    if (!form.security_id || !form.price_source_id || !form.price_date || !form.price) {
      setError("Please fill in all required fields (Security, Price Source, Date, and Price).");
      setSaving(false);
      return;
    }
    
    try {
      const payload = {
        security_id: Number(form.security_id),
        price_source_id: Number(form.price_source_id),
        price_date: form.price_date,
        price: Number(form.price),
        market_cap: form.market_cap === "" || form.market_cap === null || form.market_cap === undefined ? 0 : Number(form.market_cap),
        addl_notes: form.addl_notes === "" ? null : (form.addl_notes || null),
        price_currency: form.price_currency || "USD",
      };
      
      // Only include security_price_id for edit operations
      if (isEdit) {
        payload.security_price_id = Number(id);
        await api.updateSecurityPrice(id, payload);
      } else {
        await api.createSecurityPrice(payload);
      }
      navigate("/security-prices", { replace: true });
    } catch (e) {
      setError("Failed to save price.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>{isEdit ? "Edit Security Price" : "Add Security Price"}</h1>
      </div>
      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflowY: "auto", overflowX: "auto", marginTop: 12, maxHeight: "calc(100vh - 160px)", padding: 16 }}>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 12, maxWidth: 640 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Security *</span>
          <select
            value={form.security_id}
            onChange={(e) => onChange("security_id", e.target.value === "" ? "" : Number(e.target.value))}
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          >
            <option value="">Select a security…</option>
            {securities.map((s) => (
              <option key={s.security_id} value={s.security_id}>
                {(s.ticker || s.name)} ({s.security_id}){s.name ? ` – ${s.name}` : ""}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Price Source *</span>
          <select
            value={form.price_source_id}
            onChange={(e) => onChange("price_source_id", e.target.value === "" ? "" : Number(e.target.value))}
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          >
            <option value="">Select a source…</option>
            {platforms.map((ep) => (
              <option key={ep.external_platform_id} value={ep.external_platform_id}>
                {ep.name} ({ep.external_platform_id})
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Price Date *</span>
          <input
            type="date"
            value={form.price_date}
            onChange={(e) => onChange("price_date", e.target.value)}
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Price *</span>
          <input
            type="number"
            step="any"
            value={form.price}
            onChange={(e) => onChange("price", e.target.value === "" ? "" : Number(e.target.value))}
            onWheel={(e) => { e.preventDefault(); e.stopPropagation(); }}
            inputMode="decimal"
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Market Cap</span>
          <input
            type="number"
            step="any"
            value={form.market_cap}
            onChange={(e) => onChange("market_cap", e.target.value === "" ? "" : Number(e.target.value))}
            onWheel={(e) => { e.preventDefault(); e.stopPropagation(); }}
            inputMode="decimal"
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Additional Notes</span>
          <textarea
            value={form.addl_notes}
            onChange={(e) => onChange("addl_notes", e.target.value)}
            rows={3}
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1", resize: "vertical" }}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Currency *</span>
          <input
            type="text"
            value={form.price_currency}
            onChange={(e) => onChange("price_currency", e.target.value)}
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>

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
    </div>
  );
}
