// src/pages/Login.jsx
import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const { login } = useAuth();
  const [form, setForm] = React.useState({ email: "", password: "" });
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login(form.email, form.password);
      // expects: { access_token, user: { id, email } }
      login(res);
      navigate(state?.from?.pathname || "/", { replace: true });
    } catch {
      // show email/password invalid
      setError("User email/password is not valid.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "grid", placeItems: "center", minHeight: "100vh" }}>
      <form onSubmit={onSubmit} style={{ width: 360, background: "white", padding: 24, borderRadius: 12, boxShadow: "0 8px 24px rgba(0,0,0,0.1)", display: "grid", gap: 12 }}>
        <h2 style={{ margin: 0 }}>Sign in</h2>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            placeholder="jane.doe@example.com"
            autoComplete="email"
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Password</span>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            placeholder="••••••••"
            autoComplete="current-password"
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>
        {error && <div style={{ color: "#b91c1c", fontSize: 14 }}>{error}</div>}
        <button type="submit" disabled={loading} style={{ marginTop: 8, background: "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer", opacity: loading ? 0.7 : 1 }}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}