import { NavLink } from "react-router";
import { useAuth } from "../../auth/AuthContext";
import type { ReactNode } from "react";

const finance = [["/finance-analyst","Dashboard"],["/finance-analyst/opportunity-shortlisting","Opportunity Shortlisting"],["/finance-analyst/assigning-an-expert","Assigning an Expert"]];
const expert = [["/investigation-expert","Dashboard"],["/investigation-expert/my-investigations","My Investigations"]];
export default function AppShell({ children }: { children: ReactNode }) { const { user, logout } = useAuth(); const links = user?.role === "FINANCE_ANALYST" ? finance : expert;
 return <div className="app-shell"><aside className="sidebar"><div className="logo"><div className="logo__cat">CAT</div><div className="logo__divider"/><div className="logo__text">Cost<br/>Intelligence Platform</div></div><nav>{user?.role==="FINANCE_ANALYST"&&<span className="nav-section">FINANCE ANALYST</span>}{links.map(([to,label],i)=><NavLink key={`${label}-${i}`} to={to} end={i===0} className={({isActive})=>isActive?"active":""}><i>{["▦","◎","♙","◉","⊘","↗","◇"][i]}</i>{label}</NavLink>)}</nav><div className="sidebar-foot"><button onClick={logout}>↩ &nbsp; Logout</button></div></aside><div className="workspace"><header className="topbar"><div><span className="status-dot"/> Live data</div><div className="user-avatar">{user?.name.split(" ").map(x=>x[0]).join("")}</div><div><b>{user?.name}</b><small>{user?.role.replace("_"," ")}</small></div></header>{children}</div></div> }
