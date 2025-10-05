const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getAuthHeader() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const url = `${BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }
  const contentType = res.headers.get("content-type") || "";
  return contentType.includes("application/json") ? res.json() : res.text();
}

export const api = {
  login: (email, password) =>
    request("/users/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  getHoldings: () => request("/holdings", { method: "GET" }),

  // Securities endpoints (adjust paths to your backend)
  listSecurities: () => request("/securities", { method: "GET" }),
  getSecurity: (id) => request(`/securities/${id}`, { method: "GET" }),
  createSecurity: (payload) => request("/securities/", { method: "POST", body: JSON.stringify(payload) }),
  updateSecurity: (id, payload) => request(`/securities/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteSecurity: (id) => request(`/securities/${id}`, { method: "DELETE" }),

  // Portfolio endpoints
  listPortfolios: () => request("/portfolios", { method: "GET" }),
  getPortfolio: (id) => request(`/portfolios/${id}`, { method: "GET" }),
  createPortfolio: (payload) => request("/portfolios/", { method: "POST", body: JSON.stringify(payload) }),
  updatePortfolio: (id, payload) => request(`/portfolios/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deletePortfolio: (id) => request(`/portfolios/${id}`, { method: "DELETE" }),
  createPortfoliosBulk: (payloadList) => request("/portfolios/bulk", { method: "POST", body: JSON.stringify(payloadList) }),

  // External Platforms
  listExternalPlatforms: () => request("/external-platforms", { method: "GET" }),
  getExternalPlatform: (id) => request(`/external-platforms/${id}`, { method: "GET" }),
  createExternalPlatform: (payload) => request("/external-platforms/", { method: "POST", body: JSON.stringify(payload) }),
  updateExternalPlatform: (id, payload) => request(`/external-platforms/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteExternalPlatform: (id) => request(`/external-platforms/${id}`, { method: "DELETE" }),

  // Users
  listUsers: () => request("/users", { method: "GET" }),
  getUser: (id) => request(`/users/${id}`, { method: "GET" }),
  createUser: (payload) => request("/users/", { method: "POST", body: JSON.stringify(payload) }),
  updateUser: (id, payload) => request(`/users/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteUser: (id) => request(`/users/${id}`, { method: "DELETE" }),

  // Holdings
  listHoldings: () => request("/holdings", { method: "GET" }),
  getHolding: (id) => request(`/holdings/${id}`, { method: "GET" }),
  createHolding: (payload) => request("/holdings/", { method: "POST", body: JSON.stringify(payload) }),
  updateHolding: (id, payload) => request(`/holdings/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteHolding: (id) => request(`/holdings/${id}`, { method: "DELETE" }),

  // Security Prices
  listSecurityPrices: () => request("/security-prices", { method: "GET" }),
  getSecurityPrice: (id) => request(`/security-prices/${id}`, { method: "GET" }),
  createSecurityPrice: (payload) => request("/security-prices/", { method: "POST", body: JSON.stringify(payload) }),
  updateSecurityPrice: (id, payload) => request(`/security-prices/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteSecurityPrice: (id) => request(`/security-prices/${id}`, { method: "DELETE" }),

  // Transactions
  listTransactions: () => request("/transactions", { method: "GET" }),
  listTransactionsFull: () => request("/transactions", { method: "GET" }),
  getTransaction: (id) => request(`/transactions/${id}`, { method: "GET" }),
  getTransactionFormData: () => request("/transactions/form-data", { method: "GET" }),
  createTransaction: (payload) => request("/transactions/", { method: "POST", body: JSON.stringify(payload) }),
  updateTransaction: (id, payload) => request(`/transactions/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteTransaction: (id) => request(`/transactions/${id}`, { method: "DELETE" }),
  // Maintenance
  recalculateTransactionFees: () => request("/transactions/recalculate-fees", { method: "POST" }),
};