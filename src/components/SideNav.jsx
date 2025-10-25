import React from "react";
import { NavLink, useLocation } from "react-router-dom";

export default function SideNav({ open, onClose }) {
  const location = useLocation();
  const [secOpen, setSecOpen] = React.useState(() =>
    location.pathname.startsWith("/securities")
  );
  const [pfOpen, setPfOpen] = React.useState(() =>
    location.pathname.startsWith("/portfolios")
  );
  const [userOpen, setUserOpen] = React.useState(() =>
    location.pathname.startsWith("/users")
  );
  const [tpOpen, setTpOpen] = React.useState(() =>
    location.pathname.startsWith("/external-platforms")
  );
  const [txOpen, setTxOpen] = React.useState(() =>
    location.pathname.startsWith("/transactions")
  );
  const [holdOpen, setHoldOpen] = React.useState(() =>
    location.pathname === "/" || location.pathname.startsWith("/holdings")
  );

  const mainItems = [
    { to: "/", label: "Home" },
  ];

  const isActive = (path) =>
    location.pathname === path || location.pathname.startsWith(`${path}/`);

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.35)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
          transition: "opacity 150ms ease",
          zIndex: 900,
        }}
      />
      <aside
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          height: "100vh",
          width: 260,
          background: "#ffffff",
          boxShadow: "2px 0 12px rgba(0,0,0,0.2)",
          transform: open ? "translateX(0)" : "translateX(-100%)",
          transition: "transform 200ms ease",
          paddingTop: 56,
          zIndex: 1000,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {mainItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onClose}
            style={({ isActive: active }) => ({
              padding: "12px 16px",
              textDecoration: "none",
              color: active ? "#0f172a" : "#334155",
              background: active ? "#e2e8f0" : "transparent",
              fontWeight: active ? 700 : 500,
              display: "block",
            })}
          >
            {item.label}
          </NavLink>
        ))}

        {/* Holdings submenu */}
        <button
          type="button"
          onClick={() => setHoldOpen((v) => !v)}
          aria-expanded={holdOpen}
          style={{
            textAlign: "left",
            padding: "12px 16px",
            background: isActive("/holdings") || location.pathname === "/" ? "#e2e8f0" : "transparent",
            color: "#334155",
            border: "none",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          Holdings {holdOpen ? "▾" : "▸"}
        </button>
        <div
          style={{
            maxHeight: holdOpen ? 400 : 0,
            overflow: "hidden",
            transition: "max-height 200ms ease",
          }}
        >
          {[
            { to: "/holdings", label: "List" },
            { to: "/holdings/new", label: "Add" },
          ].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              style={({ isActive: active }) => ({
                display: "block",
                padding: "10px 24px",
                textDecoration: "none",
                color: active ? "#0f172a" : "#475569",
                background: active ? "#e2e8f0" : "transparent",
                fontWeight: active ? 700 : 500,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* Transactions submenu */}
        <button
          type="button"
          onClick={() => setTxOpen((v) => !v)}
          aria-expanded={txOpen}
          style={{
            textAlign: "left",
            padding: "12px 16px",
            background: isActive("/transactions") ? "#e2e8f0" : "transparent",
            color: "#334155",
            border: "none",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          Transactions {txOpen ? "▾" : "▸"}
        </button>
        <div
          style={{
            maxHeight: txOpen ? 400 : 0,
            overflow: "hidden",
            transition: "max-height 200ms ease",
          }}
        >
          {[
            { to: "/transactions", label: "List" },
            { to: "/transactions/new", label: "Add" },
          ].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              style={({ isActive: active }) => ({
                display: "block",
                padding: "10px 24px",
                textDecoration: "none",
                color: active ? "#0f172a" : "#475569",
                background: active ? "#e2e8f0" : "transparent",
                fontWeight: active ? 700 : 500,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* Securities submenu */}
        <button
          type="button"
          onClick={() => setSecOpen((v) => !v)}
          aria-expanded={secOpen}
          style={{
            textAlign: "left",
            padding: "12px 16px",
            background: isActive("/securities") ? "#e2e8f0" : "transparent",
            color: "#334155",
            border: "none",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          Securities {secOpen ? "▾" : "▸"}
        </button>

        <div
          style={{
            maxHeight: secOpen ? 400 : 0,
            overflow: "hidden",
            transition: "max-height 200ms ease",
          }}
        >
          {[
            { to: "/securities", label: "List" },
            { to: "/securities/new", label: "Add" },
          ].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              style={({ isActive: active }) => ({
                display: "block",
                padding: "10px 24px",
                textDecoration: "none",
                color: active ? "#0f172a" : "#475569",
                background: active ? "#e2e8f0" : "transparent",
                fontWeight: active ? 700 : 500,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* Users submenu */}
        <button
          type="button"
          onClick={() => setUserOpen((v) => !v)}
          aria-expanded={userOpen}
          style={{
            textAlign: "left",
            padding: "12px 16px",
            background: isActive("/users") ? "#e2e8f0" : "transparent",
            color: "#334155",
            border: "none",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          Users {userOpen ? "▾" : "▸"}
        </button>
        <div
          style={{
            maxHeight: userOpen ? 400 : 0,
            overflow: "hidden",
            transition: "max-height 200ms ease",
          }}
        >
          {[
            { to: "/users", label: "List" },
            { to: "/users/new", label: "Add" },
          ].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              style={({ isActive: active }) => ({
                display: "block",
                padding: "10px 24px",
                textDecoration: "none",
                color: active ? "#0f172a" : "#475569",
                background: active ? "#e2e8f0" : "transparent",
                fontWeight: active ? 700 : 500,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* Portfolios submenu */}
        <button
          type="button"
          onClick={() => setPfOpen((v) => !v)}
          aria-expanded={pfOpen}
          style={{
            textAlign: "left",
            padding: "12px 16px",
            background: isActive("/portfolios") ? "#e2e8f0" : "transparent",
            color: "#334155",
            border: "none",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          Portfolios {pfOpen ? "▾" : "▸"}
        </button>
        <div
          style={{
            maxHeight: pfOpen ? 400 : 0,
            overflow: "hidden",
            transition: "max-height 200ms ease",
          }}
        >
          {[
            { to: "/portfolios", label: "List" },
            { to: "/portfolios/new", label: "Add" },
          ].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              style={({ isActive: active }) => ({
                display: "block",
                padding: "10px 24px",
                textDecoration: "none",
                color: active ? "#0f172a" : "#475569",
                background: active ? "#e2e8f0" : "transparent",
                fontWeight: active ? 700 : 500,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* External Platforms submenu */}
        <button
          type="button"
          onClick={() => setTpOpen((v) => !v)}
          aria-expanded={tpOpen}
          style={{
            textAlign: "left",
            padding: "12px 16px",
            background: isActive("/external-platforms") ? "#e2e8f0" : "transparent",
            color: "#334155",
            border: "none",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          External Platforms {tpOpen ? "▾" : "▸"}
        </button>
        <div
          style={{
            maxHeight: tpOpen ? 400 : 0,
            overflow: "hidden",
            transition: "max-height 200ms ease",
          }}
        >
          {[
            { to: "/external-platforms", label: "List" },
            { to: "/external-platforms/new", label: "Add" },
          ].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              style={({ isActive: active }) => ({
                display: "block",
                padding: "10px 24px",
                textDecoration: "none",
                color: active ? "#0f172a" : "#475569",
                background: active ? "#e2e8f0" : "transparent",
                fontWeight: active ? 700 : 500,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </aside>
    </>
  );
}