const _envBase = (import.meta.env.VITE_API_BASE_URL || "").trim();
let BASE_URL;
if (_envBase) {
  // Explicit override provided at build time (e.g., via .env or Docker ARG)
  BASE_URL = _envBase;
} else if (typeof window !== "undefined") {
  // In browser: use same-origin in production (served by FastAPI),
  // and localhost:8000 during Vite dev for local testing.
  BASE_URL = import.meta.env && import.meta.env.DEV ? "http://localhost:8000" : window.location.origin;
} else {
  // Non-browser contexts (tests/SSR) default to local backend
  BASE_URL = "http://localhost:8000";
}

function getAuthHeader() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  // Auto-prefix /api for relative paths not already under /api
  let p = path || "";
  if (!/^https?:\/\//i.test(p)) {
    if (!p.startsWith("/api")) {
      p = `/api${p.startsWith("/") ? "" : "/"}${p}`;
    }
  }
  const url = `${BASE_URL}${p.startsWith("/") ? "" : "/"}${p}`;
  console.log("Request:", url, options);
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
  createSecuritiesBulkUnique: (payloadList) => request("/securities/bulk-unique", { method: "POST", body: JSON.stringify(payloadList) }),
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
  // Holdings maintenance
  recalcHoldings: (date) => request(`/holdings/recalculate`, { method: "POST", body: JSON.stringify({ date }) }),

  // Security Prices
  listSecurityPrices: (date) => request(`/security-prices${date ? `?date=${encodeURIComponent(date)}` : ""}`, { method: "GET" }),
  listSecurityPricesWithFilters: (fromDate, toDate, ticker) => {
    const params = new URLSearchParams();
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    if (ticker && ticker.trim()) params.append('ticker', ticker.trim());
    const queryString = params.toString();
    return request(`/security-prices${queryString ? `?${queryString}` : ""}`, { method: "GET" });
  },
  getSecurityPrice: (id) => request(`/security-prices/${id}`, { method: "GET" }),
  createSecurityPrice: (payload) => request("/security-prices/", { method: "POST", body: JSON.stringify(payload) }),
  updateSecurityPrice: (id, payload) => request(`/security-prices/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteSecurityPrice: (id) => request(`/security-prices/${id}`, { method: "DELETE" }),
  // Admin maintenance
  downloadPrices: (fromDate, toDate, tickers) => {
    const payload = {};
    if (fromDate) payload.from_date = fromDate;
    if (toDate) payload.to_date = toDate;
    if (tickers && Array.isArray(tickers) && tickers.length > 0) {
      payload.tickers = tickers.filter(t => t && t.trim()).map(t => t.trim());
    }
    return request(`/security-prices/download`, { method: "POST", body: JSON.stringify(payload) });
  },

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
  // Performance comparison
  getLinkedTransactionPairs: () => request("/transactions/linked-pairs", { method: "GET" }),
  getPerformanceComparison: (pairId, fromDate, toDate, options = {}) => {
    const params = new URLSearchParams();
    params.append('from_date', fromDate);
    params.append('to_date', toDate);
    return request(`/transactions/performance-comparison/${pairId}?${params.toString()}`, { method: "GET", ...options });
  },
};