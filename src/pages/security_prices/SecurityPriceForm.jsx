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
        <SearchableSecurityDropdown
          label="Security *"
          securities={securities}
          value={form.security_id}
          onChange={(securityId) => onChange("security_id", securityId)}
          required={true}
        />

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

// Searchable security dropdown component
function SearchableSecurityDropdown({ label, securities, value, onChange, required = false }) {
  const [searchTerm, setSearchTerm] = React.useState("");
  const [isOpen, setIsOpen] = React.useState(false);
  const [selectedSecurity, setSelectedSecurity] = React.useState(null);
  const dropdownRef = React.useRef(null);

  // Find selected security when value changes
  React.useEffect(() => {
    const selected = securities.find(s => s.security_id === value);
    setSelectedSecurity(selected || null);
    if (selected) {
      setSearchTerm(selected.ticker || selected.name || "");
    } else {
      setSearchTerm("");
    }
  }, [value, securities]);

  // Filter securities based on search term
  const filteredSecurities = React.useMemo(() => {
    if (!searchTerm) return securities;
    const term = searchTerm.toLowerCase();
    return securities.filter(s => 
      (s.ticker && s.ticker.toLowerCase().includes(term)) ||
      (s.name && s.name.toLowerCase().includes(term)) ||
      s.security_id.toString().includes(term)
    );
  }, [securities, searchTerm]);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        // Reset search term to selected security if no selection made
        if (selectedSecurity) {
          setSearchTerm(selectedSecurity.ticker || selectedSecurity.name || "");
        } else {
          setSearchTerm("");
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [selectedSecurity]);

  const handleInputChange = (e) => {
    setSearchTerm(e.target.value);
    setIsOpen(true);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
    setSearchTerm(""); // Clear search to show all options
  };

  const handleSecuritySelect = (security) => {
    setSelectedSecurity(security);
    setSearchTerm(security.ticker || security.name || "");
    setIsOpen(false);
    onChange(security.security_id);
  };

  const handleClear = () => {
    setSelectedSecurity(null);
    setSearchTerm("");
    setIsOpen(false);
    onChange("");
  };

  const displayText = selectedSecurity 
    ? `${selectedSecurity.ticker || selectedSecurity.name} (${selectedSecurity.security_id})${selectedSecurity.name && selectedSecurity.ticker ? ` – ${selectedSecurity.name}` : ""}`
    : "";

  return (
    <div ref={dropdownRef} style={{ position: "relative", display: "grid", gap: 6 }}>
      <span>{label}</span>
      <div style={{ position: "relative" }}>
        <input
          type="text"
          value={isOpen ? searchTerm : displayText}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder="Search for a security..."
          required={required}
          style={{ 
            padding: 10, 
            paddingRight: selectedSecurity ? 35 : 10,
            borderRadius: 8, 
            border: "1px solid #cbd5e1",
            width: "100%",
            boxSizing: "border-box"
          }}
        />
        {selectedSecurity && (
          <button
            type="button"
            onClick={handleClear}
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
          >
            ×
          </button>
        )}
        {isOpen && filteredSecurities.length > 0 && (
          <div style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            background: "white",
            border: "1px solid #cbd5e1",
            borderRadius: 8,
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            maxHeight: 200,
            overflowY: "auto",
            zIndex: 1000
          }}>
            {filteredSecurities.map((security) => (
              <div
                key={security.security_id}
                onClick={() => handleSecuritySelect(security)}
                style={{
                  padding: "8px 12px",
                  cursor: "pointer",
                  borderBottom: "1px solid #f1f5f9",
                  backgroundColor: selectedSecurity?.security_id === security.security_id ? "#f1f5f9" : "white"
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = "#f8fafc"}
                onMouseLeave={(e) => e.target.style.backgroundColor = selectedSecurity?.security_id === security.security_id ? "#f1f5f9" : "white"}
              >
                <div style={{ fontWeight: 500 }}>
                  {security.ticker || security.name} ({security.security_id})
                </div>
                {security.name && security.ticker && (
                  <div style={{ fontSize: "0.875rem", color: "#64748b" }}>
                    {security.name}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {isOpen && filteredSecurities.length === 0 && searchTerm && (
          <div style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            background: "white",
            border: "1px solid #cbd5e1",
            borderRadius: 8,
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            padding: "8px 12px",
            color: "#64748b",
            zIndex: 1000
          }}>
            No securities found matching "{searchTerm}"
          </div>
        )}
      </div>
    </div>
  );
}
