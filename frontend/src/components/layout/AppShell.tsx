import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation } from "react-router";
import { useAuth } from "../../auth/AuthContext";
const finance = [["/finance-analyst","Dashboard"],["/finance-analyst/opportunity-shortlisting","Opportunity Shortlisting"],["/finance-analyst/assigning-an-expert","Assigning an Expert"]];
const expert = [["/investigation-expert","Dashboard"],["/investigation-expert/my-investigations","My Investigations"]];
const executive = [["/executive","Guidance Home"],["/executive/plants","Plant Comparison"],["/executive/products","Product Comparison"],["/executive/categories","Category Comparison"],["/executive/reports","Executive Report"]];
export default function AppShell({ children }: { children: ReactNode }) {const {user,logout}=useAuth();const location=useLocation();const componentLink=location.pathname.startsWith("/executive/components/")?[[location.pathname,"Component Comparison"]]:[];const links=user?.role==="FINANCE_ANALYST"?finance:user?.role==="INVESTIGATION_EXPERT"?expert:[...executive,...componentLink];return <div className="app-shell"><RouteLoader key={location.pathname}/><aside className="sidebar"><div className="logo"><div className="logo__cat">CAT</div><div className="logo__divider"/><div className="logo__text">Cost<br/>Intelligence Platform</div></div><nav><span className="nav-section">{user?.role.replaceAll("_"," ")}</span>{links.map(([to,label],i)=><NavLink key={`${label}-${i}`} to={to} end={i===0||to==="/executive/products"} className={({isActive})=>isActive?"active":""}><i>{["▦","◎","♙","◉","◇","◇"][i]}</i>{label}</NavLink>)}</nav><div className="sidebar-foot"><button onClick={logout}>↩ &nbsp; Logout</button></div></aside><div className="workspace"><header className="topbar"><div><span className="status-dot"/> Live data</div><div className="user-avatar">{user?.name.split(" ").map(x=>x[0]).join("")}</div><div><b>{user?.name}</b><small>{user?.role.replaceAll("_"," ")}</small></div></header><Breadcrumbs path={location.pathname}/>{children}</div></div>}

function Breadcrumbs({path}:{path:string}){
 const finance=path.startsWith("/finance-analyst"),isExecutive=path.startsWith("/executive"),root=finance?"/finance-analyst":isExecutive?"/executive":"/investigation-expert";
 const labels:Record<string,string>={
  "/finance-analyst/opportunity-shortlisting":"Opportunity Shortlisting",
  "/finance-analyst/assigning-an-expert":"Assigning an Expert",
  "/finance-analyst/monitor-outcome":"Monitor Outcome",
  "/finance-analyst/opportunity-rejection":"Opportunity Rejection",
  "/finance-analyst/cost-saving":"Cost Saving",
  "/finance-analyst/monitor-learnings":"Monitor Learnings",
  "/investigation-expert/my-investigations":"My Investigations"
 };
 if(isExecutive){
  const segments=path.split("/").filter(Boolean); const executiveLabels:Record<string,string>={plants:"Plant Comparison",products:"Product Comparison",categories:"Category Comparison",components:"Component Comparison",opportunities:"Opportunity Brief",reports:"Executive Report"};
  const items:{label:string;to?:string}[]=[{label:"Guidance Home",to:path===root?undefined:root}];
  if(path!==root){const section=segments[1];items.push({label:executiveLabels[section]??"Workspace",to:segments.length>2&&section==="products"?"/executive/products":undefined});if(segments.length>2)items.push({label:segments[2]});}
  return <nav className="app-breadcrumbs" aria-label="Breadcrumb"><ol>{items.map((item,index)=><li key={`${item.label}-${index}`}>{item.to?<Link to={item.to}>{item.label}</Link>:<span aria-current="page">{item.label}</span>}</li>)}</ol></nav>;
 }
 const detail=path.startsWith("/finance-analyst/opportunities/")||path.startsWith("/investigation-expert/my-investigations/");
 const items:{label:string;to?:string}[]=[{label:"Dashboard",to:path===root?undefined:root}];
 if(detail&&finance)items.push({label:"Opportunity Shortlisting",to:"/finance-analyst/opportunity-shortlisting"},{label:"Opportunity Details"});
 else if(detail)items.push({label:"My Investigations",to:"/investigation-expert/my-investigations"},{label:"Investigation Details"});
 else if(path!==root)items.push({label:labels[path]??"Workspace"});
 return <nav className="app-breadcrumbs" aria-label="Breadcrumb"><ol>{items.map((item,index)=><li key={`${item.label}-${index}`}>{item.to?<Link to={item.to}>{item.label}</Link>:<span aria-current="page">{item.label}</span>}</li>)}</ol></nav>
}
function RouteLoader(){const[visible,setVisible]=useState(true);useEffect(()=>{const timer=window.setTimeout(()=>setVisible(false),500);return()=>window.clearTimeout(timer)},[]);return visible?<div className="route-loader" role="status" aria-label="Loading live data"><i/><span>Syncing live data…</span></div>:null}
