import React from "react";

const AuthContext = React.createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = React.useState(() => {
    const u = localStorage.getItem("user");
    return u ? JSON.parse(u) : null;
  });

  const isAuthenticated = !!user;

  const login = ({ access_token, user }) => {
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("user", JSON.stringify(user));
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}