import { useEffect, useState } from "react";
import { Link } from "react-router";
import ExecutiveFilters from "../../components/executive/ExecutiveFilters";
import { ExecutiveError, ExecutiveLoading } from "../../components/executive/ExecutiveState";
import { money, percent } from "../../components/executive/executiveFormat";
import { getExecutiveCategories, type ExecutiveFilters as Filters } from "../../services/executive";
import type { EquipmentCategoriesResponse } from "../../types/executive";

const symbols: Record<string, string> = {
  excavators: "⌁", "motor-graders": "⌇", "wheel-loaders": "◫",
  dozers: "▰", "off-highway-trucks": "▱",
};

export default function CategoryComparisonPage() {
  const [filters, setFilters] = useState<Filters>({ period: "FY26", scope: "enterprise" });
  const [result, setResult] = useState<EquipmentCategoriesResponse | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { let active = true; getExecutiveCategories(filters).then(next => {
    if (active) { setResult(next); setError(""); }
  }).catch(requestError => active && setError(requestError instanceof Error ? requestError.message : "Category data could not be loaded")); return () => { active = false; }; }, [filters]);

  return <main className="executive-page category-page">
    <div className="executive-heading"><div><span className="eyebrow">EQUIPMENT PORTFOLIO</span><h1>Category cost performance</h1><p>Compare cost exposure and savings opportunity across CAT equipment categories.</p></div><ExecutiveFilters value={filters} onChange={setFilters} asOfDate={result?.as_of_date}/></div>
    {error ? <ExecutiveError message={error}/> : !result ? <ExecutiveLoading/> : <>
      <section className="equipment-category-grid">{result.categories.map(category => <Link key={category.category_id} to={`/executive/categories/${category.category_id}`} className="equipment-category-card">
        <header><span>{symbols[category.category_id] ?? "◇"}</span><b className={`executive-chip ${category.priority.toLowerCase()}`}>{category.priority}</b></header>
        <small>EQUIPMENT CATEGORY</small><h2>{category.category_name}</h2><strong>{money(Number(category.potential_savings))}</strong><p>Potential savings across {category.product_count} configured products</p>
        <div><span><small>Annual spend</small><b>{money(Number(category.annual_spend))}</b></span><span><small>Cost variance</small><b className="metric-risk">{percent(Number(category.cost_variance_percent))}</b></span></div>
        <footer><span>{category.high_priority_opportunities} high-priority opportunities</span><b>View products →</b></footer>
      </Link>)}</section>
      <section className="executive-table-panel category-ranking"><div className="section-title"><div><span className="eyebrow">CATEGORY RANKING</span><h2>Equipment-family opportunity</h2></div><span>Backend-ranked by potential savings</span></div><div className="table-wrap"><table><thead><tr><th>Category</th><th>Products</th><th>Annual spend</th><th>Potential savings</th><th>Variance</th><th>High priority</th><th>Confidence</th><th>Primary opportunity driver</th></tr></thead><tbody>{result.categories.map(category => <tr key={category.category_id}><td><Link to={`/executive/categories/${category.category_id}`}><strong>{category.category_name}</strong><small>{category.category_id}</small></Link></td><td>{category.product_count}</td><td>{money(Number(category.annual_spend))}</td><td><strong>{money(Number(category.potential_savings))}</strong></td><td className="metric-risk">{percent(Number(category.cost_variance_percent))}</td><td>{category.high_priority_opportunities}</td><td>{percent(Number(category.confidence) * 100)}</td><td>{category.primary_opportunity_driver ?? "—"}</td></tr>)}</tbody></table></div></section>
    </>}
  </main>;
}
