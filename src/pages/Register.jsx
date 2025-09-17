import React from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api/client.js";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = React.useState({ first_name: "", last_name: "", email: "", password: "" });
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.createUser({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        password: form.password,
      });
      navigate("/login", { replace: true });
    } catch (e) {
      setError("Failed to create account.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ display: "grid", placeItems: "center", minHeight: "100vh" }}>
      <form onSubmit={onSubmit} style={{ width: 420, background: "white", padding: 24, borderRadius: 12, boxShadow: "0 8px 24px rgba(0,0,0,0.1)", display: "grid", gap: 12 }}>
        <h2 style={{ margin: 0 }}>Create account</h2>
        <label style={{ display: "grid", gap: 6 }}>
          <span>First Name</span>
          <input type="text" value={form.first_name} onChange={(e)=>setForm(f=>({...f, first_name: e.target.value}))} required style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Last Name</span>
          <input type="text" value={form.last_name} onChange={(e)=>setForm(f=>({...f, last_name: e.target.value}))} required style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Email</span>
          <input type="email" value={form.email} onChange={(e)=>setForm(f=>({...f, email: e.target.value}))} required style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Password</span>
          <input type="password" value={form.password} onChange={(e)=>setForm(f=>({...f, password: e.target.value}))} required style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
        </label>
        {error && <div style={{ color: "#b91c1c", fontSize: 14 }}>{error}</div>}
        <button type="submit" disabled={saving} style={{ marginTop: 8, background: "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer", opacity: saving ? 0.7 : 1 }}>
          {saving ? "Creating..." : "Create account"}
        </button>
        <div style={{ fontSize: 14 }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </form>
    </div>
  );
}
