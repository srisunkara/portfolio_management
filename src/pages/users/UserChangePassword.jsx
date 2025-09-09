import React from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client.js";

export default function UserChangePassword() {
  const navigate = useNavigate();
  const [users, setUsers] = React.useState([]);
  const [selectedId, setSelectedId] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirm, setConfirm] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");
  const [success, setSuccess] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const list = await api.listUsers();
        if (alive) setUsers(list || []);
      } catch (e) {
        if (alive) setError("Failed to load users.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const canSubmit = selectedId && password && confirm && password === confirm && !saving;

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (!selectedId) {
      setError("Please select a user.");
      return;
    }
    setSaving(true);
    try {
      // Minimal payload: backend will hash if 'password' present
      await api.updateUser(selectedId, { password });
      setSuccess("Password updated successfully.");
      // optional: navigate back after short delay
      setTimeout(() => navigate("/users", { replace: true }), 600);
    } catch (e) {
      setError("Failed to update password.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Change User Password</h1>
      <form onSubmit={onSubmit} style={{ background: "white", padding: 16, borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", display: "grid", gap: 12, maxWidth: 520 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>User</span>
          <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} required style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}>
            <option value="">Select a user…</option>
            {users.map((u) => (
              <option key={u.user_id} value={u.user_id}>
                {u.first_name} {u.last_name} {u.email ? `(${u.email})` : ""}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>New Password</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={4} placeholder="Enter new password" style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Confirm Password</span>
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={4} placeholder="Re-enter new password" style={{ padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }} />
        </label>

        {error && <div style={{ color: "#b91c1c" }}>{error}</div>}
        {success && <div style={{ color: "#065f46" }}>{success}</div>}

        <div style={{ display: "flex", gap: 8 }}>
          <button type="submit" disabled={!canSubmit} style={{ background: "#0f172a", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: canSubmit ? "pointer" : "not-allowed", opacity: saving ? 0.8 : 1 }}>
            {saving ? "Saving..." : "Update Password"}
          </button>
          <button type="button" onClick={() => navigate(-1)} style={{ background: "#e2e8f0", color: "#0f172a", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer" }}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
