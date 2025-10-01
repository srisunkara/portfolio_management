// src/pages/users/MyProfile.jsx
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client.js";
import { useAuth } from "../../context/AuthContext.jsx";

export default function MyProfile() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [me, setMe] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const uid = user?.user_id || user?.id || user?.userId;
        let data = null;
        if (uid) {
          try {
            data = await api.getUser(uid);
          } catch (_) {
            // Fallback: list and find
            const all = await api.listUsers();
            data = (all || []).find((u) => (u.user_id ?? u.id) === uid) || null;
          }
        }
        if (alive) setMe(data || null);
      } catch (e) {
        if (alive) setError("Failed to load profile.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [user]);

  if (loading) return <div>Loading profile...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  const uid = user?.user_id || user?.id || user?.userId;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>My Profile</h1>
        <button
          type="button"
          onClick={() => uid && navigate(`/users/${uid}/edit`)}
          style={{ background: "#0f172a", color: "white", padding: "8px 12px", borderRadius: 8, border: "none", cursor: "pointer" }}
        >
          Edit Profile
        </button>
        <Link to="/users/change-password" style={{ background: "#e2e8f0", color: "#0f172a", padding: "8px 12px", borderRadius: 8, textDecoration: "none" }}>
          Change Password
        </Link>
      </div>

      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflow: "auto", marginTop: 12, maxHeight: "calc(100vh - 160px)", padding: 16 }}>
        {me ? (
          <div style={{ display: "grid", gap: 12, maxWidth: 720 }}>
            <Row label="User Id" value={me.user_id ?? me.id} />
            <Row label="First Name" value={me.first_name} />
            <Row label="Last Name" value={me.last_name} />
            <Row label="Email" value={me.email} />
            <Row label="Created" value={me.created_ts} />
            <Row label="Last Updated" value={me.last_updated_ts} />
          </div>
        ) : (
          <div style={{ color: "#64748b" }}>No user found.</div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", alignItems: "center", gap: 8 }}>
      <div style={{ fontWeight: 600, color: "#334155" }}>{label}</div>
      <div>{value ?? "-"}</div>
    </div>
  );
}
