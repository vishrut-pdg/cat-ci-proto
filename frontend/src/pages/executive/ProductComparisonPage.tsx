import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import ExecutiveFilters from "../../components/executive/ExecutiveFilters";
import { ExecutiveError, ExecutiveLoading } from "../../components/executive/ExecutiveState";
import { money, percent } from "../../components/executive/executiveFormat";
import { getExecutiveCategories, getExecutiveProducts, type ExecutiveFilters as Filters } from "../../services/executive";
import type { EquipmentCategory, ProductExecutiveItem } from "../../types/executive";

export default function ProductComparisonPage() {
  const [search] = useSearchParams();
  const initialCategory = search.get("categoryId") ?? "";
  const [filters, setFilters] = useState<Filters>({ period: "FY26", scope: "enterprise", category_id: initialCategory || undefined });
  const [items, setItems] = useState<ProductExecutiveItem[] | null>(null);
  const [categories, setCategories] = useState<EquipmentCategory[]>([]);
  const [date, setDate] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { let active = true; Promise.all([getExecutiveProducts(filters), getExecutiveCategories({ period: filters.period, scope: filters.scope })]).then(([products, categoryResult]) => {
    if (active) { setItems(products.items); setDate(products.as_of_date); setCategories(categoryResult.categories); setError(""); }
  }).catch(requestError => active && setError(requestError instanceof Error ? requestError.message : "Product data could not be loaded")); return () => { active = false; }; }, [filters]);
  return <main className="executive-page">
    <div className="executive-heading"><div><span className="eyebrow">PRODUCT PORTFOLIO</span><h1>Product opportunities</h1><p>Compare specific equipment models across the enterprise or within one equipment category.</p></div><div className="product-comparison-controls"><label>Equipment category<select value={filters.category_id ?? ""} onChange={event => setFilters(current => ({ ...current, category_id: event.target.value || undefined }))}><option value="">All categories</option>{categories.map(category => <option key={category.category_id} value={category.category_id}>{category.category_name}</option>)}</select></label><ExecutiveFilters value={filters} onChange={next => setFilters({ ...next, category_id: filters.category_id })} asOfDate={date}/></div></div>
    {error ? <ExecutiveError message={error}/> : !items ? <ExecutiveLoading/> : items.length === 0 ? <div className="executive-state">No products match this equipment category.</div> : <section className="product-grid">{items.map(item => <Link to={`/executive/products/${item.product_id}`} className="product-card" key={item.product_id}><header><span>{item.category_name}</span><b className={`executive-chip ${item.priority.toLowerCase()}`}>{item.priority}</b></header><h2>{item.product_name}</h2><strong>{money(Number(item.potential_savings))}</strong><small>Potential savings</small><div><span><small>Average unit cost</small><b>{money(Number(item.average_unit_cost), false)}</b></span><span><small>Cost variance</small><b className="metric-risk">{percent(Number(item.variance_percent))}</b></span></div><footer><span>High: {item.highest_cost_plant ?? "—"}</span><span>Low: {item.lowest_cost_plant ?? "—"}</span><b>View product →</b></footer></Link>)}</section>}
  </main>;
}
