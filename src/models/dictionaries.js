// src/models/dictionaries.js
// Common dictionaries for UI rendering and form controls

export const TRANSACTION_TYPES = {
  B: "Buy",
  S: "Sell",
};

export const TRANSACTION_TYPE_OPTIONS = Object.entries(TRANSACTION_TYPES).map(([code, label]) => ({ code, label }));

export function transactionTypeLabel(code) {
  if (code == null || code === "") return "-";
  const key = String(code).toUpperCase();
  return TRANSACTION_TYPES[key] || code;
}
