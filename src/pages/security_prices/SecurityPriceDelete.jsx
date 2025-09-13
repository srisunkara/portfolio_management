import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

// General pages
import Login from "./pages/Login.jsx";
import Home from "./pages/Home.jsx";
import TopBar from "./components/TopBar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
// Users pages
import UsersList from "./pages/users/UsersList.jsx";
import UserForm from "./pages/users/UserForm.jsx";
import UserEdit from "./pages/users/UserEdit.jsx";
import UserDelete from "./pages/users/UserDelete.jsx";
// Roles pages
import RolesList from "./pages/roles/RolesList.jsx";
import RoleForm from "./pages/roles/RoleForm.jsx";
import RoleEdit from "./pages/roles/RoleEdit.jsx";
import RoleDelete from "./pages/roles/RoleDelete.jsx";
// Clients pages
import ClientsList from "./pages/clients/ClientsList.jsx";
import ClientForm from "./pages/clients/ClientForm.jsx";
import ClientEdit from "./pages/clients/ClientEdit.jsx";
import ClientDelete from "./pages/clients/ClientDelete.jsx";
// Accounts pages
import AccountsList from "./pages/accounts/AccountsList.jsx";
import AccountForm from "./pages/accounts/AccountForm.jsx";
import AccountEdit from "./pages/accounts/AccountEdit.jsx";
import AccountDelete from "./pages/accounts/AccountDelete.jsx";
// Trading Platforms pages
import TradingPlatformsList from "./pages/external_platforms/ExternalPlatformsList.jsx";
import TradingPlatformForm from "./pages/external_platforms/ExternalPlatformForm.jsx";
import TradingPlatformEdit from "./pages/external_platforms/ExternalPlatformEdit.jsx";
import TradingPlatformDelete from "./pages/external_platforms/ExternalPlatformDelete.jsx";
// Security Prices pages
import SecurityPricesList from "./pages/security_prices/SecurityPricesList.jsx";
import SecurityPriceForm from "./pages/security_prices/SecurityPriceForm.jsx";
import SecurityPriceEdit from "./pages/security_prices/SecurityPriceEdit.jsx";
import SecurityPriceDelete from "./pages/security_prices/SecurityPriceDelete.jsx";

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#f7f7f7" }}>
      {isAuthenticated && (
        <TopBar />
      )}
      <div style={{ flex: 1, padding: isAuthenticated ? "72px 16px 16px" : "16px" }}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
          {/* Users */}
          <Route path="/users" element={<ProtectedRoute><UsersList /></ProtectedRoute>} />
          <Route path="/users/new" element={<ProtectedRoute><UserForm /></ProtectedRoute>} />
          <Route path="/users/:id/edit" element={<ProtectedRoute><UserEdit /></ProtectedRoute>} />
          <Route path="/users/:id/delete" element={<ProtectedRoute><UserDelete /></ProtectedRoute>} />
          {/* Roles */}
          <Route path="/roles" element={<ProtectedRoute><RolesList /></ProtectedRoute>} />
          <Route path="/roles/new" element={<ProtectedRoute><RoleForm /></ProtectedRoute>} />
          <Route path="/roles/:id/edit" element={<ProtectedRoute><RoleEdit /></ProtectedRoute>} />
          <Route path="/roles/:id/delete" element={<ProtectedRoute><RoleDelete /></ProtectedRoute>} />
          {/* Clients */}
          <Route path="/clients" element={<ProtectedRoute><ClientsList /></ProtectedRoute>} />
          <Route path="/clients/new" element={<ProtectedRoute><ClientForm /></ProtectedRoute>} />
          <Route path="/clients/:id/edit" element={<ProtectedRoute><ClientEdit /></ProtectedRoute>} />
          <Route path="/clients/:id/delete" element={<ProtectedRoute><ClientDelete /></ProtectedRoute>} />
          {/* Accounts */}
          <Route path="/accounts" element={<ProtectedRoute><AccountsList /></ProtectedRoute>} />
          <Route path="/accounts/new" element={<ProtectedRoute><AccountForm /></ProtectedRoute>} />
          <Route path="/accounts/:id/edit" element={<ProtectedRoute><AccountEdit /></ProtectedRoute>} />
          <Route path="/accounts/:id/delete" element={<ProtectedRoute><AccountDelete /></ProtectedRoute>} />
          {/* Trading Platforms */}
          <Route path="/trading-platforms" element={<ProtectedRoute><TradingPlatformsList /></ProtectedRoute>} />
          <Route path="/trading-platforms/new" element={<ProtectedRoute><TradingPlatformForm /></ProtectedRoute>} />
          <Route path="/trading-platforms/:id/edit" element={<ProtectedRoute><TradingPlatformEdit /></ProtectedRoute>} />
          <Route path="/trading-platforms/:id/delete" element={<ProtectedRoute><TradingPlatformDelete /></ProtectedRoute>} />
          {/* Security Prices */}
          <Route path="/security-prices" element={<ProtectedRoute><SecurityPricesList /></ProtectedRoute>} />
          <Route path="/security-prices/new" element={<ProtectedRoute><SecurityPriceForm /></ProtectedRoute>} />
          <Route path="/security-prices/:id/edit" element={<ProtectedRoute><SecurityPriceEdit /></ProtectedRoute>} />
          <Route path="/security-prices/:id/delete" element={<ProtectedRoute><SecurityPriceDelete /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
        </Routes>
      </div>
    </div>
  );
}