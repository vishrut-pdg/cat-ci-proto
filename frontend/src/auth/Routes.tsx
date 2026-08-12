import { Navigate, Outlet } from "react-router";
import { useAuth, type Role } from "./AuthContext";
export function ProtectedRoute() { return useAuth().user ? <Outlet /> : <Navigate to="/login" replace />; }
export function RoleRoute({ role }: { role: Role }) { const { user } = useAuth(); return user?.role === role ? <Outlet /> : <Navigate to={user?.role === "FINANCE_ANALYST" ? "/finance-analyst" : "/investigation-expert"} replace />; }
