import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import ExecutiveFilters from "../../components/executive/ExecutiveFilters";
import { ExecutiveError, ExecutiveLoading } from "../../components/executive/ExecutiveState";
import { money, percent } from "../../components/executive/executiveFormat";
import { getExecutiveCategories, type ExecutiveFilters as Filters } from "../../services/executive";
import type { CategoriesResponse } from "../../types/executive";

const colors = ["#0968d2", "#ef8d19", "#e3b20a", "#16a36a", "#7c62c9"];

export default function CategoryComparisonPage() {
  const [search] = useSearchParams();
  const productId = search.get("productId") ?? undefined;
  const [filters, setFilters] = useState<Filters>({ period: "FY26", scope: "enterprise", product_id: productId });
  const [result, setResult] = useState<CategoriesResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getExecutiveCategories(filters).then(next => {
      if (active) { setResult(next); setError(""); }
    }).catch(err => active && setError(err instanceof Error ? err.message : "Request failed"));
    return () => { active = false; };
  }, [filters]);

  return <main className="executive-page">
    <div className="executive-heading">
      <div><span className="eyebrow">COST GAP ANALYSIS</span><h1>Category comparison</h1><p>Structured cost drivers explain the current portfolio gap against its benchmark.</p></div>
      <ExecutiveFilters value={filters} onChange={next => setFilters({ ...next, product_id: productId })} asOfDate={result?.as_of_date}/>
    </div>
    {error ? <ExecutiveError message={error}/> : !result ? <ExecutiveLoading/> : <>
      <section className="category-summary">
        <div><small>EXPLAINED COST GAP</small><strong>{money(Number(result.overall_gap), false)}</strong><span>Weighted USD per unit</span></div>
        <div><small>DRIVER CATEGORIES</small><strong>{result.items.length}</strong><span>Controlled driver codes</span></div>
        <div><small>RECONCILIATION</small><strong>{percent(Number(result.contribution_total))}</strong><span className={Math.abs(Number(result.contribution_total) - 100) < .1 ? "metric-good" : "metric-risk"}>Category contribution total</span></div>
      </section>
      <section className="category-layout">
        <div className="executive-table-panel">
          <div className="section-title"><div><span className="eyebrow">DRIVER BREAKDOWN</span><h2>What is driving the cost gap?</h2></div></div>
          <div className="table-wrap"><table><thead><tr><th>Category</th><th>Benchmark</th><th>Comparison</th><th>Gap</th><th>Contribution</th></tr></thead><tbody>{result.items.map((item, index) => <tr key={item.category_code}><td><span className="category-dot" style={{ background: colors[index % colors.length] }}/><strong>{item.category}</strong><small>{item.category_code}</small></td><td>{money(Number(item.benchmark_cost), false)}</td><td>{money(Number(item.comparison_cost), false)}</td><td className="metric-risk">+{money(Number(item.gap), false)}</td><td><strong>{percent(Number(item.contribution_percent))}</strong></td></tr>)}</tbody></table></div>
        </div>
        <aside className="driver-contribution-card"><span className="eyebrow">CONTRIBUTION</span><h2>Concentration of explained gap</h2><p>Calculated from seeded opportunity evidence—not display labels or an LLM.</p><div>{result.items.map((item, index) => <section key={item.category_code}><header><span><i style={{ background: colors[index % colors.length] }}/>{item.category}</span><b>{percent(Number(item.contribution_percent))}</b></header><div><i style={{ width: `${Math.min(100, Number(item.contribution_percent))}%`, background: colors[index % colors.length] }}/></div></section>)}</div></aside>
      </section>
    </>}
  </main>;
}
