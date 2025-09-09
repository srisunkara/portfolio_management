import React from "react";
import { api } from "../../api/client.js";

export default function Holdings() {
  const [data, setData] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const res = await api.getHoldings();
        if (isMounted) setData(res);
      } catch (e) {
        if (isMounted) setError("Failed to load holdings.");
      } finally {
        if (isMounted) setLoading(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) return <div>Loading holdings...</div>;
  if (error) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Holdings</h1>
      <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", overflow: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 720 }}>
          <thead style={{ background: "#f1f5f9" }}>
            <tr>
              <th style={{ textAlign: "left", padding: 12 }}>Holding Id</th>
              <th style={{ textAlign: "left", padding: 12 }}>Holding Dt</th>
              <th style={{ textAlign: "left", padding: 12 }}>Portfolio Id</th>
              <th style={{ textAlign: "left", padding: 12 }}>Security Id</th>
              <th style={{ textAlign: "left", padding: 12 }}>Quantity</th>
              <th style={{ textAlign: "left", padding: 12 }}>Price</th>
              <th style={{ textAlign: "left", padding: 12 }}>Market Value</th>
            </tr>
          </thead>
          <tbody>
            {data.map((h) => (
              <tr key={h.holding_id ?? JSON.stringify(h)} style={{ borderTop: "1px solid #e2e8f0" }}>
                <td style={{ padding: 12 }}>{h.holding_id}</td>
                <td style={{ padding: 12 }}>{h.holding_dt}</td>
                <td style={{ padding: 12 }}>{h.portfolio_id}</td>
                <td style={{ padding: 12 }}>{h.security_id}</td>
                <td style={{ padding: 12 }}>{h.quantity}</td>
                <td style={{ padding: 12 }}>{h.price}</td>
                <td style={{ padding: 12 }}>{h.market_value}</td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan="7" style={{ padding: 16, textAlign: "center", color: "#64748b" }}>
                  No holdings found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}