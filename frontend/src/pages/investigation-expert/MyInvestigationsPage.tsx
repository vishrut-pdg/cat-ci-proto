import { useEffect,useState } from "react";
import { Link } from "react-router";
import { apiGet } from "../../services/api";
import { PageTitle } from "../finance-analyst/FinanceDashboard";

interface Investigation{id:string;opportunity_id:string;status:string;due_at:string;part_name:string;part_number:string;plant_name:string;country:string;potential_savings:number;priority:string}
const money=(n:number)=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",notation:"compact",maximumFractionDigits:1}).format(n);

export default function MyInvestigationsPage(){
 const [items,setItems]=useState<Investigation[]>([]),[error,setError]=useState("");
 useEffect(()=>{apiGet<{items:Investigation[]}>("/investigations").then(x=>setItems(x.items)).catch(e=>setError(e.message))},[]);
 return <main><PageTitle title="My Investigations" sub="Build an evidence-backed root-cause case and turn it into an actionable recommendation."/>{error&&<div className="error-box">{error}</div>}<section className="panel"><div className="panel-head"><div><h2>Active investigation portfolio</h2><p>Assigned opportunities ordered by due date.</p></div></div><div className="investigation-grid">{items.map(x=><Link className="investigation-card" to={`/investigation-expert/my-investigations/${x.opportunity_id}`} key={x.id}><div><span className={`chip ${x.priority.toLowerCase()}`}>{x.priority}</span><span className="chip neutral">{x.status.replaceAll("_"," ")}</span></div><h3>{x.part_name}</h3><p>{x.part_number} · {x.plant_name}, {x.country}</p><div className="investigation-meta"><div><small>POTENTIAL SAVINGS</small><b>{money(x.potential_savings)}</b></div><div><small>DUE</small><b>{x.due_at}</b></div></div><span className="open-link">Open investigation →</span></Link>)}</div>{!items.length&&!error&&<div className="empty">No investigations are currently assigned to you.</div>}</section></main>
}
