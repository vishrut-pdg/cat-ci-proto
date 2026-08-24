import { useEffect, useState } from "react";
import { Link } from "react-router";
import ExecutiveFilters from "../../components/executive/ExecutiveFilters";
import { ExecutiveError, ExecutiveLoading } from "../../components/executive/ExecutiveState";
import { money, percent } from "../../components/executive/executiveFormat";
import { getExecutiveProducts, type ExecutiveFilters as Filters } from "../../services/executive";
import type { ProductExecutiveItem } from "../../types/executive";

export default function ProductComparisonPage() {
  const [filters, setFilters] = useState<Filters>({ period: "FY26", scope: "enterprise" }); const [items, setItems] = useState<ProductExecutiveItem[] | null>(null); const [date, setDate] = useState(""); const [error, setError] = useState("");
  useEffect(() => { let active = true; getExecutiveProducts(filters).then(result => { if (active) { setItems(result.items); setDate(result.as_of_date); setError(""); } }).catch(err => active && setError(err instanceof Error ? err.message : "Request failed")); return () => { active = false; }; }, [filters]);
  return <main className="executive-page"><div className="executive-heading"><div><span className="eyebrow">PORTFOLIO COMPARISON</span><h1>Product opportunities</h1><p>Each part is attributed once to a stable primary compatible model.</p></div><ExecutiveFilters value={filters} onChange={setFilters} asOfDate={date}/></div>{error ? <ExecutiveError message={error}/> : !items ? <ExecutiveLoading/> : <section className="product-grid">{items.map(item => <Link to={`/executive/products/${item.product_id}`} className="product-card" key={item.product_id}><header><span>{item.equipment_family}</span><b className={`executive-chip ${item.priority.toLowerCase()}`}>{item.priority}</b></header><h2>{item.product_name}</h2><strong>{money(Number(item.potential_savings))}</strong><small>Potential savings</small><div><span><small>Average unit cost</small><b>{money(Number(item.average_unit_cost), false)}</b></span><span><small>Cost variance</small><b className="metric-risk">{percent(Number(item.variance_percent))}</b></span></div><footer><span>High: {item.highest_cost_plant ?? "—"}</span><span>Low: {item.lowest_cost_plant ?? "—"}</span><b>View product →</b></footer></Link>)}</section>}</main>;
}
