// src/components/TopBar.jsx
import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function TopBar() {
  const { user, logout } = useAuth();

  // Keep menu font size consistent across Dashboard, dropdown triggers, and submenu items
  const MENU_FONT_SIZE = 16;
  const menuStyle = { display: "flex", gap: 8, marginLeft: 16 };
  const linkStyle = ({ isActive }) => ({
    color: isActive ? "#ffffff" : "#d1d5db",
    textDecoration: "none",
    padding: "6px 10px",
    borderRadius: 6,
    background: isActive ? "rgba(255,255,255,0.15)" : "transparent",
    fontWeight: 600,
    fontSize: MENU_FONT_SIZE,
  });

  return (
    <div style={{ position: "fixed", top: 0, left: 0, right: 0, height: 56, background: "#0f172a", color: "white", display: "flex", alignItems: "center", padding: "0 12px", boxShadow: "0 2px 8px rgba(0,0,0,0.15)", zIndex: 1000 }}>
      <div style={{ fontWeight: 700, marginRight: 8 }}>Portfolio Management</div>

      {/* Primary menu */}
      <nav style={menuStyle}>
        <NavLink to="/" style={linkStyle} end>Dashboard</NavLink>

        <Dropdown label="Holdings">
          <MenuLink to="/holdings">List</MenuLink>
          <MenuLink to="/holdings/new">Add</MenuLink>
        </Dropdown>

        <Dropdown label="Transactions">
          <MenuLink to="/transactions">List</MenuLink>
          <MenuLink to="/transactions/new">Add</MenuLink>
        </Dropdown>

        <Dropdown label="Securities">
          <MenuLink to="/securities">List</MenuLink>
          <MenuLink to="/securities/new">Add</MenuLink>
        </Dropdown>

        <Dropdown label="Security Prices">
          <MenuLink to="/security-prices">List</MenuLink>
          <MenuLink to="/security-prices/new">Add</MenuLink>
        </Dropdown>

        <Dropdown label="Portfolios">
          <MenuLink to="/portfolios">List</MenuLink>
          <MenuLink to="/portfolios/new">Add</MenuLink>
        </Dropdown>

        <Dropdown label="Users">
          <MenuLink to="/users">My Profile</MenuLink>
          {/* Admin-only: List Users */}
          { (user?.is_admin || user?.isAdmin) ? (
            <MenuLink to="/users/all">List Users</MenuLink>
          ) : null }
          <MenuLink to="/users/change-password">Change Password</MenuLink>
        </Dropdown>

        <Dropdown label="External Platforms">
          <MenuLink to="/external-platforms">List</MenuLink>
          <MenuLink to="/external-platforms/new">Add</MenuLink>
        </Dropdown>

      </nav>

      <div style={{ marginLeft: "auto", display: "flex", gap: 12, alignItems: "center" }}>
        <div style={{ opacity: 0.9, fontSize: 14 }}>
          {(() => {
            if (!user) return "";
            const first = user.first_name || user.firstName || "";
            const last = user.last_name || user.lastName || "";
            const combined = `${first} ${last}`.replace(/\s+/g, " ").trim();
            const altName = user.full_name || user.fullName || user.name || "";
            const displayName = (combined && combined !== "") ? combined : (altName || "");
            const email = user.email || user.username || "";
            return displayName ? `${displayName} — ${email}` : email;
          })()}
        </div>
        <button onClick={logout} style={{ background: "#ef4444", border: "none", color: "white", padding: "6px 10px", borderRadius: 6, cursor: "pointer" }}>
          Logout
        </button>
      </div>
    </div>
  );
}

function Dropdown({ label, children }) {
  const [open, setOpen] = React.useState(false);
  const closeTimer = React.useRef(null);

  const openMenu = () => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
    setOpen(true);
  };
  const scheduleClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = setTimeout(() => setOpen(false), 200);
  };
  const closeNow = () => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
    setOpen(false);
  };

  // Inject onSelect to submenu items so clicking a link closes the dropdown immediately
  const enhancedChildren = React.Children.map(children, (child) => {
    if (!React.isValidElement(child)) return child;
    return React.cloneElement(child, { onSelect: closeNow });
  });

  return (
    <div
      onMouseEnter={openMenu}
      onMouseLeave={scheduleClose}
      style={{ position: "relative" }}
    >
      <button
        type="button"
        onClick={() => (open ? scheduleClose() : openMenu())}
        style={{
          color: "#d1d5db",
          background: "transparent",
          border: "1px solid rgba(255,255,255,0.2)",
          borderRadius: 6,
          padding: "6px 10px",
          cursor: "pointer",
          fontWeight: 600,
          fontSize: 16,
        }}
        aria-expanded={open}
      >
        {label} ▾
      </button>
      <div
        onMouseEnter={openMenu}
        onMouseLeave={scheduleClose}
        style={{
          position: "absolute",
          top: "100%",
          left: 0,
          background: "#0b1222",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: 8,
          minWidth: 160,
          padding: 6,
          boxShadow: "0 4px 14px rgba(0,0,0,0.3)",
          display: open ? "grid" : "none",
          gap: 4,
          zIndex: 1200,
        }}
      >
        {enhancedChildren}
      </div>
    </div>
  );
}

function MenuLink({ to, children, onSelect }) {
  return (
    <NavLink
      to={to}
      onClick={onSelect}
      style={({ isActive }) => ({
        color: isActive ? "#ffffff" : "#e5e7eb",
        textDecoration: "none",
        padding: "8px 10px",
        borderRadius: 6,
        background: isActive ? "rgba(255,255,255,0.1)" : "transparent",
        whiteSpace: "nowrap",
        fontWeight: 600,
        fontSize: 16,
      })}
    >
      {children}
    </NavLink>
  );
}