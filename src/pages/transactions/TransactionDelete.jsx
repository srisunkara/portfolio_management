import React from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { api } from "../../api/client.js";

export default function TransactionDelete() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  const onDelete = async () => {
    setError("");
    setLoading(true);
    try {
      await api.deleteTransaction(id);
      navigate("/transactions", { replace: true });
    } catch {
      setError("Failed to delete transaction.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 520 }}>
      <h1 style={{ marginTop: 0 }}>Delete Transaction</h1>
      <p>Are you sure you want to delete transaction with ID {id}?</p>
      {error && <div style={{ color: "#b91c1c" }}>{error}</div>}
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={onDelete} disabled={loading} style={{ background: "#b91c1c", color: "white", border: "none", padding: "10px 12px", borderRadius: 8, cursor: "pointer", opacity: loading ? 0.7 : 1 }}>
          {loading ? "Deleting..." : "Delete"}
        </button>
        <Link to="/transactions" style={{ background: "#e2e8f0", color: "#0f172a", padding: "10px 12px", borderRadius: 8, textDecoration: "none" }}>
          Cancel
        </Link>
      </div>
    </div>
  );
}
