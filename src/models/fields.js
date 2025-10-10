// src/models/fields.js

// Reusable registry: define models once, use everywhere.
// Types: "integer" | "number" | "string" | "boolean" | "date" | "date-time"
export const modelFieldDefs = {
  SecurityDtl: [
    { name: "ticker", type: "string" },
    { name: "name", type: "string" },
    { name: "company_name", type: "string" },
    { name: "security_currency", type: "string" },
    { name: "is_private", type: "boolean" },
    { name: "created_ts", type: "string", format: "date-time", readOnly: true },
    { name: "last_updated_ts", type: "string", format: "date-time", readOnly: true },
    { name: "security_id", type: "integer", readOnly: true },
  ],
  // ... existing code ...
  // Portfolio model (used by UI pages similar to Securities)
  PortfolioDtl: [
    { name: "portfolio_id", type: "integer", readOnly: true },
    { name: "user_id", type: "integer" },
    { name: "name", type: "string" },
    { name: "open_date", type: "date" },
    { name: "close_date", type: "date" },
    { name: "created_ts", type: "string", format: "date-time", readOnly: true },
    { name: "last_updated_ts", type: "string", format: "date-time", readOnly: true },
  ],
  ExternalPlatformDtl: [
    { name: "external_platform_id", type: "integer", readOnly: true },
    { name: "name", type: "string" },
    { name: "platform_type", type: "string" },
    { name: "created_ts", type: "string", format: "date-time", readOnly: true },
    { name: "last_updated_ts", type: "string", format: "date-time", readOnly: true },
  ],
  UserDtl: [
    { name: "user_id", type: "integer", readOnly: true },
    { name: "first_name", type: "string" },
    { name: "last_name", type: "string" },
    { name: "email", type: "string" },
    { name: "is_admin", type: "boolean", readOnly: true },
    // We do not expose password_hash in forms; for create/edit, accept an optional 'password' input field
    { name: "created_ts", type: "string", format: "date-time", readOnly: true },
    { name: "last_updated_ts", type: "string", format: "date-time", readOnly: true },
  ],
  HoldingDtl: [
    { name: "holding_dt", type: "date" },
    { name: "quantity", type: "number" },
    { name: "price", type: "number" },
    { name: "avg_price", type: "number" },
    { name: "market_value", type: "number" },
    { name: "security_price_dt", type: "date" },
    { name: "holding_cost_amt", type: "number" },
    { name: "unreal_gain_loss_amt", type: "number" },
    { name: "unreal_gain_loss_perc", type: "number" },
    { name: "created_ts", type: "string", format: "date-time", readOnly: true },
    { name: "last_updated_ts", type: "string", format: "date-time", readOnly: true },
  ],
  SecurityPriceDtl: [
    { name: "price_date", type: "date" },
    { name: "price", type: "number" },
    { name: "market_cap", type: "number" },
    { name: "addl_notes", type: "string" },
    { name: "price_currency", type: "string" },
    { name: "last_updated_ts", type: "string", format: "date-time", readOnly: true },
  ],
  TransactionDtl: [
    { name: "transaction_id", type: "integer", readOnly: true },
    { name: "portfolio_id", type: "integer" },
    { name: "security_id", type: "integer" },
    { name: "external_platform_id", type: "integer" },
    { name: "transaction_date", type: "date" },
    { name: "transaction_type", type: "string" },
    { name: "transaction_qty", type: "number" },
    { name: "total_inv_amt", type: "number" },
    { name: "transaction_price", type: "number" },
    { name: "transaction_fee", type: "number", default: 0.0 },
    { name: "transaction_fee_percent", type: "number", default: 0.0 },
    { name: "management_fee", type: "number", default: 0.0 },
    { name: "management_fee_percent", type: "number", default: 0.0 },
    { name: "external_manager_fee", type: "number", default: 0.0 },
    { name: "external_manager_fee_percent", type: "number", default: 0.0 },
    { name: "carry_fee", type: "number", default: 0.0 },
    { name: "carry_fee_percent", type: "number", default: 0.0 },
    { name: "rel_transaction_id", type: "integer" },
    { name: "created_ts", type: "string", format: "date-time", readOnly: true },
    { name: "last_updated_ts", type: "string", format: "date-time", readOnly: true },
  ],
  TransactionFullView: [
    { name: "portfolio_name", type: "string" },
    { name: "security_ticker", type: "string" },
    { name: "security_name", type: "string" },
    { name: "transaction_date", type: "date" },
    { name: "transaction_type", type: "string" },
    { name: "total_inv_amt", type: "number" },
    { name: "transaction_qty", type: "number" },
    { name: "transaction_price", type: "number" },
    { name: "transaction_fee_percent", type: "number" },
    { name: "transaction_fee", type: "number" },
    { name: "management_fee_percent", type: "number" },
    { name: "management_fee", type: "number" },
    { name: "external_manager_fee_percent", type: "number" },
    { name: "external_manager_fee", type: "number" },
    { name: "carry_fee_percent", type: "number" },
    { name: "carry_fee", type: "number" },
    { name: "gross_amount", type: "number" },
    { name: "total_fee", type: "number" },
    { name: "net_amount", type: "number" },
    { name: "created_ts", type: "string", format: "date-time", readOnly: true },
    { name: "last_updated_ts", type: "string", format: "date-time", readOnly: true },
    { name: "external_platform_name", type: "string" },
    { name: "user_full_name", type: "string" },
    { name: "transaction_id", type: "integer", readOnly: true },
    { name: "rel_transaction_id", type: "integer" },
    { name: "portfolio_id", type: "integer" },
    { name: "user_id", type: "integer" },
    { name: "security_id", type: "integer" },
    { name: "external_platform_id", type: "integer" },
  ],
 };

// Return ordered fields (in model-defined order)
export function getOrderedFields(modelName) {
  const def = modelFieldDefs[modelName];
  if (!def) throw new Error(`Unknown model: ${modelName}`);
  return def;
}

// For create/edit forms: skip date/time fields and readOnly fields
export function formFieldsForAction(modelName, action /* 'create' | 'edit' */) {
  const fields = getOrderedFields(modelName);
  return fields.filter((f) => {
    if (f.readOnly) return false;
    // Keep date fields visible in forms; only exclude date-time and read-only
    if (f.format === "date-time" || f.type === "date-time") return false;
    return true;
  });
}

// Helpers for rendering and form coercion
export function labelize(s) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function defaultValueForType(type) {
  if (type === "boolean") return false;
  if (type === "integer" || type === "number") return "";
  return "";
}

export function coerceValue(val, field) {
  if (val === "" || val == null) return null;
  if (field.type === "integer") return Number.isFinite(val) ? Math.trunc(val) : Number(val);
  if (field.type === "number") return Number(val);
  if (field.type === "boolean") return !!val;
  return val;
}

import { transactionTypeLabel } from "./dictionaries.js";

export function renderCell(value, field) {
  if (value == null) return "-";
  if (field.format === "date-time" || field.type === "date-time") {
    const d = new Date(value);
    return isNaN(d) ? String(value) : d.toLocaleString();
  }
  if (field.type === "date") {
    // Avoid timezone shifts: if value is YYYY-MM-DD, show as-is
    if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return value;
    }
    const d = new Date(value);
    return isNaN(d) ? String(value) : d.toLocaleDateString();
  }
  // Format numeric fields with commas and 2 decimals across the app
  if (field?.type === "number") {
    const num = typeof value === "number" ? value : Number(value);
    if (!Number.isFinite(num)) return String(value);
    try {
      return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } catch (e) {
      // Fallback in unlikely environments without Intl support
      return num.toFixed(2);
    }
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (field?.name === "transaction_type") return transactionTypeLabel(value);
  return String(value);
}