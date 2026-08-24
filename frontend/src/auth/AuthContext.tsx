import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { apiRequest } from "../services/api";

export type Role = "FINANCE_ANALYST" | "INVESTIGATION_EXPERT" | "EXECUTIVE";
export interface DemoUser { id: string; name: string; role: Role; email: string }
interface AuthValue { user: DemoUser | null; login: (id: string, password: string) => Promise<DemoUser>; logout: () => void }
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<DemoUser | null>(() => {
    try { return JSON.parse(localStorage.getItem("cat_ci_user") ?? "null"); } catch { return null; }
  });
  const value = useMemo<AuthValue>(() => ({ user,
    login: async (id, password) => {
      const result = await apiRequest<{ token: string; user: DemoUser }>("/auth/login", "POST", { user_id: id, password });
      localStorage.setItem("cat_ci_token", result.token); localStorage.setItem("cat_ci_user", JSON.stringify(result.user)); setUser(result.user); return result.user;
    },
    logout: () => { localStorage.removeItem("cat_ci_token"); localStorage.removeItem("cat_ci_user"); setUser(null); },
  }), [user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("useAuth requires AuthProvider"); return value; }
