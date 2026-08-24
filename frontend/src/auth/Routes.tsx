import { Navigate, Outlet } from "react-router";
import { useAuth, type Role } from "./AuthContext";
export function ProtectedRoute() { return useAuth().user ? <Outlet /> : <Navigate to="/login" replace />; }
const roleHome: Record<Role, string> = { FINANCE_ANALYST: "/finance-analyst", INVESTIGATION_EXPERT: "/investigation-expert", EXECUTIVE: "/executive" };
export function RoleRoute({ role }: { role: Role }) { const { user } = useAuth(); return user?.role === role ? <Outlet /> : <Navigate to={user ? roleHome[user.role] : "/login"} replace />; }
