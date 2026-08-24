import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import ExecutiveFilters from "../../components/executive/ExecutiveFilters";
import { ExecutiveError, ExecutiveLoading } from "../../components/executive/ExecutiveState";
import { money, percent } from "../../components/executive/executiveFormat";
import { getExecutiveCategories, getExecutiveProducts, type ExecutiveFilters as Filters } from "../../services/executive";
import type { EquipmentCategory, ProductExecutiveItem } from "../../types/executive";

export default function CategoryDetailPage() {
  const { categoryId = "" } = useParams();
  const [filters, setFilters] = useState<Filters>({ period: "FY26", scope: "enterprise", category_id: categoryId });
  const [category, setCategory] = useState<EquipmentCategory | null>(null);
  const [products, setProducts] = useState<ProductExecutiveItem[] | null>(null);
  const [asOfDate, setAsOfDate] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { let active = true; const scoped = { ...filters, category_id: categoryId }; Promise.all([getExecutiveCategories(scoped), getExecutiveProducts(scoped)]).then(([categoryResult, productResult]) => {
    if (active) { const match = categoryResult.categories.find(item => item.category_id === categoryId) ?? null; setCategory(match); setProducts(productResult.items); setAsOfDate(productResult.as_of_date); setError(match ? "" : "Equipment category not found"); }
  }).catch(requestError => active && setError(requestError instanceof Error ? requestError.message : "Category data could not be loaded")); return () => { active = false; }; }, [categoryId, filters]);
  if (error) return <main className="executive-page"><ExecutiveError message={error}/></main>;
  if (!products || !category) return <main className="executive-page"><ExecutiveLoading/></main>;
  return <main className="executive-page category-detail-page">
    <Link className="product-back-link" to="/executive/categories">← Back to all categories</Link>
    <div className="executive-heading"><div><span className="eyebrow">EQUIPMENT CATEGORY · {category.category_id}</span><h1>{category.category_name}</h1><p>{category.product_count} configured products; {products.length} have current opportunity evidence totaling {money(Number(category.potential_savings))}.</p></div><ExecutiveFilters value={filters} onChange={next => setFilters({ ...next, category_id: categoryId })} asOfDate={asOfDate}/></div>
    <section className="category-summary"><div><small>ANNUAL SPEND</small><strong>{money(Number(category.annual_spend))}</strong><span>Attributed portfolio spend</span></div><div><small>POTENTIAL SAVINGS</small><strong>{money(Number(category.potential_savings))}</strong><span>Validated opportunity</span></div><div><small>COST VARIANCE</small><strong>{percent(Number(category.cost_variance_percent))}</strong><span>{category.primary_opportunity_driver ?? "No primary driver"}</span></div></section>
    <div className="section-title"><div><span className="eyebrow">PRODUCTS IN CATEGORY</span><h2>Where value is concentrated</h2></div></div>
    <section className="product-grid">{products.map(item => <Link to={`/executive/products/${item.product_id}`} className="product-card" key={item.product_id}><header><span>{item.equipment_family}</span><b className={`executive-chip ${item.priority.toLowerCase()}`}>{item.priority}</b></header><h2>{item.product_name}</h2><strong>{money(Number(item.potential_savings))}</strong><small>Potential savings</small><div><span><small>Average unit cost</small><b>{money(Number(item.average_unit_cost), false)}</b></span><span><small>Cost variance</small><b className="metric-risk">{percent(Number(item.variance_percent))}</b></span></div><footer><span>High: {item.highest_cost_plant ?? "—"}</span><span>Low: {item.lowest_cost_plant ?? "—"}</span><b>View product →</b></footer></Link>)}</section>
  </main>;
}
