import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Holdings from "./pages/holdings/Holdings.jsx";
import PortfoliosList from "./pages/portfolios/Portfolio.jsx";
import PortfolioForm from "./pages/portfolios/PortfolioForm.jsx";
import PortfolioDelete from "./pages/portfolios/PortfolioDelete.jsx";
import TransactionsList from "./pages/transactions/TransactionsList.jsx";
import TransactionForm from "./pages/transactions/TransactionForm.jsx";
import TransactionDelete from "./pages/transactions/TransactionDelete.jsx";
import HoldingForm from "./pages/holdings/HoldingForm.jsx";
import HoldingDelete from "./pages/holdings/HoldingDelete.jsx";
import TopBar from "./components/TopBar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import SecuritiesList from "./pages/securities/SecuritiesList.jsx";
import SecurityForm from "./pages/securities/SecurityForm.jsx";
import SecurityDelete from "./pages/securities/SecurityDelete.jsx";
import UsersList from "./pages/users/UsersList.jsx";
import UserForm from "./pages/users/UserForm.jsx";
import UserDelete from "./pages/users/UserDelete.jsx";
import UserChangePassword from "./pages/users/UserChangePassword.jsx";
import TradingPlatformsList from "./pages/external_platforms/ExternalPlatformsList.jsx";
import TradingPlatformForm from "./pages/external_platforms/ExternalPlatformForm.jsx";
import TradingPlatformDelete from "./pages/external_platforms/ExternalPlatformDelete.jsx";
// Add Security Prices pages
import SecurityPricesList from "./pages/security_prices/SecurityPricesList.jsx";
import SecurityPriceForm from "./pages/security_prices/SecurityPriceForm.jsx";
import SecurityPriceDelete from "./pages/security_prices/SecurityPriceDelete.jsx";

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <div style={{ display: "flex", height: "100vh", width: "100%", background: "#f7f7f7", overflow: "hidden" }}>
      {isAuthenticated && (
        <TopBar />
      )}
      <div style={{ flex: 1, padding: isAuthenticated ? "72px 16px 16px" : "16px", overflow: "hidden", display: "flex", flexDirection: "column" }}>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={<ProtectedRoute><Holdings /></ProtectedRoute>} />
          <Route path="/holdings" element={<ProtectedRoute><Holdings /></ProtectedRoute>} />
          <Route path="/holdings/new" element={<ProtectedRoute><HoldingForm mode="create" /></ProtectedRoute>} />
          <Route path="/holdings/:id/edit" element={<ProtectedRoute><HoldingForm mode="edit" /></ProtectedRoute>} />
          <Route path="/holdings/:id/delete" element={<ProtectedRoute><HoldingDelete /></ProtectedRoute>} />
          <Route path="/portfolios" element={<ProtectedRoute><PortfoliosList /></ProtectedRoute>} />
          <Route path="/portfolios/new" element={<ProtectedRoute><PortfolioForm mode="create" /></ProtectedRoute>} />
          <Route path="/portfolios/:id/edit" element={<ProtectedRoute><PortfolioForm mode="edit" /></ProtectedRoute>} />
          <Route path="/portfolios/:id/delete" element={<ProtectedRoute><PortfolioDelete /></ProtectedRoute>} />

          <Route path="/transactions" element={<ProtectedRoute><TransactionsList /></ProtectedRoute>} />
                    <Route path="/transactions/new" element={<ProtectedRoute><TransactionForm mode="create" /></ProtectedRoute>} />
                    <Route path="/transactions/:id/edit" element={<ProtectedRoute><TransactionForm mode="edit" /></ProtectedRoute>} />
                    <Route path="/transactions/:id/delete" element={<ProtectedRoute><TransactionDelete /></ProtectedRoute>} />

          {/* Securities */}
          <Route path="/securities" element={<ProtectedRoute><SecuritiesList /></ProtectedRoute>} />
          <Route path="/securities/new" element={<ProtectedRoute><SecurityForm mode="create" /></ProtectedRoute>} />
          <Route path="/securities/:id/edit" element={<ProtectedRoute><SecurityForm mode="edit" /></ProtectedRoute>} />
          <Route path="/securities/:id/delete" element={<ProtectedRoute><SecurityDelete /></ProtectedRoute>} />

          {/* Users */}
          <Route path="/users" element={<ProtectedRoute><UsersList /></ProtectedRoute>} />
          <Route path="/users/new" element={<ProtectedRoute><UserForm mode="create" /></ProtectedRoute>} />
          <Route path="/users/:id/edit" element={<ProtectedRoute><UserForm mode="edit" /></ProtectedRoute>} />
          <Route path="/users/:id/delete" element={<ProtectedRoute><UserDelete /></ProtectedRoute>} />
          <Route path="/users/change-password" element={<ProtectedRoute><UserChangePassword /></ProtectedRoute>} />

          {/* External Platforms */}
          <Route path="/external-platforms" element={<ProtectedRoute><TradingPlatformsList /></ProtectedRoute>} />
          <Route path="/external-platforms/new" element={<ProtectedRoute><TradingPlatformForm mode="create" /></ProtectedRoute>} />
          <Route path="/external-platforms/:id/edit" element={<ProtectedRoute><TradingPlatformForm mode="edit" /></ProtectedRoute>} />
          <Route path="/external-platforms/:id/delete" element={<ProtectedRoute><TradingPlatformDelete /></ProtectedRoute>} />

          {/* Security Prices */}
          <Route path="/security-prices" element={<ProtectedRoute><SecurityPricesList /></ProtectedRoute>} />
          <Route path="/security-prices/new" element={<ProtectedRoute><SecurityPriceForm /></ProtectedRoute>} />
          <Route path="/security-prices/:id/edit" element={<ProtectedRoute><SecurityPriceForm /></ProtectedRoute>} />
          <Route path="/security-prices/:id/delete" element={<ProtectedRoute><SecurityPriceDelete /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
        </Routes>
      </div>
    </div>
  );
}