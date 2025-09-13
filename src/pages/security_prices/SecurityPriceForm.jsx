import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client.js";

export default function SecurityPriceEdit() {
  const navigate = useNavigate();
  const { id } = useParams();

  const [securities, setSecurities] = React.useState([]);
  const [form, setForm] = React.useState({
    security_id: "",
    price_source: "",
    price_date: "",
    price: "",
    market_cap: "",
    price_currency: "",
  });
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [price, secs] = await Promise.all([
          api.getSecurityPrice(id),
          api.listSecurities(),
        ]);
        if (!alive) return;
        setSecurities(secs || []);
        setForm({
          security_id: price.security_id ?? "",
          price_source: price.price_source ?? "",
          price_date: typeof price.price_date === "string" ? price.price_date : new Date(price.price_date).toISOString().slice(0, 10),
          price: price.price ?? "",
          market_cap: price.market_cap ?? "",
          price_currency: price.price_currency ?? "USD",
        });
      } catch (e) {
        if (alive) setError("Failed to load price.");
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
      const payload = {
        security_price_id: Number(id),
        security_id: form.security_id === "" ? null : Number(form.security_id),
        price_source: form.price_source,
        price_date: form.price_date,
        price: form.price === "" ? null : Number(form.price),
        market_cap: form.market_cap === "" ? null : Number(form.market_cap),
        price_currency: form.price_currency,
      };
      await api.updateSecurityPrice(id, payload);
      navigate("/security-prices", { replace: true });
    } catch (e) {
      setError("Failed to update price.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Edit Security Price</h1>
      <form onSubmit={onSubmit} style={{ background: "white", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", display: "grid", gap: 12, maxWidth: 640 }}>
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
          <input
            type="text"
            value={form.price_source}
            onChange={(e) => onChange("price_source", e.target.value)}
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
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
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
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
  );
}
