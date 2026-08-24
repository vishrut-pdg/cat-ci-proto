import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import ExecutiveFilters from "../../components/executive/ExecutiveFilters";
import { ExecutiveError, ExecutiveLoading } from "../../components/executive/ExecutiveState";
import { money, percent } from "../../components/executive/executiveFormat";
import { downloadExecutiveReport, generateExecutiveReport, getExecutiveProduct, getExecutiveProductCostDrivers, getExecutiveProductTrend, sendExecutiveOpportunityToTeam, type ExecutiveFilters as Filters } from "../../services/executive";
import type { CategoriesResponse, ProductDetailResponse, ProductTrendResponse } from "../../types/executive";

const colors = ["#0968d2", "#16a36a", "#ef8d19", "#7c62c9", "#d54b58"];

function ProductTrendChart({ trend }: { trend: ProductTrendResponse }) {
  const visible = trend.series.slice(0, 5);
  const values = visible.flatMap(series => series.points.map(point => Number(point.unit_cost)));
  if (!values.length) return <div className="executive-state">No trend points are available for this product.</div>;
  const width = 760; const height = 245; const padX = 42; const padY = 24;
  const minimum = Math.min(...values) * .96; const maximum = Math.max(...values) * 1.04;
  const range = Math.max(1, maximum - minimum); const maxPoints = Math.max(...visible.map(series => series.points.length));
  const coordinates = (points: ProductTrendResponse["series"][number]["points"]) => points.map((point, index) => {
    const x = padX + (index / Math.max(1, maxPoints - 1)) * (width - padX * 2);
    const y = padY + (1 - (Number(point.unit_cost) - minimum) / range) * (height - padY * 2);
    return `${x},${y}`;
  }).join(" ");
  const labels = visible[0]?.points ?? [];
  return <div className="product-trend-chart"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Monthly attributed component cost by plant">
    {[0, .25, .5, .75, 1].map(value => <line key={value} x1={padX} x2={width - padX} y1={padY + value * (height - padY * 2)} y2={padY + value * (height - padY * 2)} className="product-grid-line"/>)}
    {visible.map((series, index) => <polyline key={series.plant_id} points={coordinates(series.points)} fill="none" stroke={colors[index]} strokeWidth="3" strokeLinejoin="round" strokeLinecap="round"/>)}
  </svg><div className="product-trend-labels"><span>{labels[0] ? new Date(labels[0].period_start).toLocaleDateString("en-US", { month: "short", year: "2-digit" }) : ""}</span><span>{labels.at(-1) ? new Date(labels.at(-1)!.period_start).toLocaleDateString("en-US", { month: "short", year: "2-digit" }) : ""}</span></div><div className="product-trend-legend">{visible.map((series, index) => <span key={series.plant_id}><i style={{ background: colors[index] }}/>{series.plant_name}</span>)}</div></div>;
}

export default function ProductDetailPage() {
  const { productId = "" } = useParams();
  const [filters, setFilters] = useState<Filters>({ period: "FY26", scope: "enterprise" });
  const [detail, setDetail] = useState<ProductDetailResponse | null>(null);
  const [trend, setTrend] = useState<ProductTrendResponse | null>(null);
  const [drivers, setDrivers] = useState<CategoriesResponse | null>(null);
  const [error, setError] = useState("");
  const [actionBusy, setActionBusy] = useState<"report" | "team" | null>(null);
  const [actionNotice, setActionNotice] = useState("");
  useEffect(() => { let active = true; Promise.all([
    getExecutiveProduct(productId, filters), getExecutiveProductTrend(productId, filters), getExecutiveProductCostDrivers(productId, filters),
  ]).then(([nextDetail, nextTrend, nextDrivers]) => { if (active) { setDetail(nextDetail); setTrend(nextTrend); setDrivers(nextDrivers); setError(""); } }).catch(requestError => active && setError(requestError instanceof Error ? requestError.message : "Product data could not be loaded")); return () => { active = false; }; }, [productId, filters]);
  const topDriver = drivers?.items[0];
  const insight = useMemo(() => detail && topDriver ? `${topDriver.category} explains ${percent(Number(topDriver.contribution_percent))} of the structured cost gap. ${detail.highest_cost_plant} is the highest-cost plant; start the drill-down with ${detail.components[0]?.component_name ?? "the leading component"}.` : "", [detail, topDriver]);
  async function generateProductReport() {
    if (!detail || actionBusy) return;
    setActionBusy("report"); setActionNotice("");
    try {
      const report = await generateExecutiveReport({ ...filters, product_id: detail.product_id });
      await downloadExecutiveReport(report);
      setActionNotice(`Report stored in MinIO and downloaded as ${report.file_name}.`);
    } catch (requestError) {
      setActionNotice(requestError instanceof Error ? requestError.message : "Report generation failed");
    } finally { setActionBusy(null); }
  }
  async function sendToTeam() {
    if (!detail || actionBusy) return;
    setActionBusy("team"); setActionNotice("");
    try {
      await sendExecutiveOpportunityToTeam(detail.lead_opportunity_id);
      setActionNotice(`Highest-value opportunity ${detail.lead_opportunity_id} was assigned to Priya Patel.`);
    } catch (requestError) {
      setActionNotice(requestError instanceof Error ? requestError.message : "Assignment failed");
    } finally { setActionBusy(null); }
  }
  return <main className="executive-page product-detail-page">
    {error ? <ExecutiveError message={error}/> : !detail || !trend || !drivers ? <ExecutiveLoading/> : <>
      <Link className="product-back-link" to="/executive/products">← Back to all products</Link>
      <div className="executive-heading product-action-heading"><div><span className="eyebrow">{detail.equipment_family} · {detail.product_id}</span><h1>{detail.product_name}</h1><p>{detail.highest_cost_plant} has the highest cost position across {detail.opportunity_count} attributed opportunities and {detail.plants.length} plants.</p></div><div className="product-heading-side"><ExecutiveFilters value={filters} onChange={setFilters} asOfDate={detail.as_of_date}/><div className="product-heading-actions"><button className="secondary" disabled={Boolean(actionBusy)} onClick={generateProductReport}>{actionBusy === "report" ? "Generating…" : "Generate report"}</button><button disabled={Boolean(actionBusy)} onClick={sendToTeam}>{actionBusy === "team" ? "Sending…" : "Send to team"}</button></div></div></div>
      {actionNotice && <div className="product-action-notice" role="status">{actionNotice}</div>}
      <section className="product-detail-hero"><div><span>POTENTIAL SAVINGS</span><strong>{money(Number(detail.potential_savings))}</strong><p>Validated portfolio opportunity</p></div><div className="product-detail-kpis"><span><small>Average unit cost</small><b>{money(Number(detail.average_unit_cost), false)}</b></span><span><small>Benchmark</small><b>{money(Number(detail.benchmark_unit_cost), false)}</b></span><span><small>Variance</small><b className="metric-risk">{percent(Number(detail.variance_percent))}</b></span><span><small>Confidence</small><b>{percent(Number(detail.confidence_score) * 100)}</b></span><span><small>Annual spend</small><b>{money(Number(detail.annual_spend))}</b></span><span><small>Annual volume</small><b>{Number(detail.annual_volume).toLocaleString()}</b></span></div></section>
      <section className="product-detail-layout"><div className="executive-table-panel product-trend-panel"><div className="section-title"><div><span className="eyebrow">12-MONTH TREND</span><h2>Attributed component cost by plant</h2></div><span>Latest: {money(Number(detail.average_unit_cost), false)}</span></div><ProductTrendChart trend={trend}/></div><aside className="product-driver-card"><span className="eyebrow">COST DRIVERS</span><h2>What explains the gap?</h2><p>{drivers.items.length} controlled driver categories reconcile to {percent(Number(drivers.contribution_total))}.</p>{drivers.items.map((driver, index) => <div className="product-driver-row" key={driver.category_code}><header><span><i style={{ background: colors[index % colors.length] }}/>{driver.category}</span><b>{percent(Number(driver.contribution_percent))}</b></header><div><i style={{ width: `${Math.min(100, Number(driver.contribution_percent))}%`, background: colors[index % colors.length] }}/></div><small>+{money(Number(driver.gap), false)} per attributed unit</small></div>)}</aside></section>
      <section className="product-ai-insight"><span>✦</span><div><small>STRUCTURED INSIGHT</small><h2>Focus the investigation where value is concentrated</h2><p>{insight}</p></div><Link to={`/executive/categories?productId=${encodeURIComponent(productId)}`}>Explore drivers →</Link></section>
      <section className="product-detail-layout tables"><div className="executive-table-panel"><div className="section-title"><div><span className="eyebrow">PLANT POSITION</span><h2>Plant comparison</h2></div></div><div className="table-wrap"><table><thead><tr><th>Plant</th><th>Unit cost</th><th>Benchmark</th><th>Variance</th><th>Savings</th></tr></thead><tbody>{detail.plants.map(plant => <tr key={plant.plant_id}><td><strong>{plant.plant_name}</strong><small>{plant.country} · {plant.plant_code}</small></td><td>{money(Number(plant.unit_cost), false)}</td><td>{money(Number(plant.benchmark_cost), false)}</td><td className="metric-risk">{percent(Number(plant.variance_percent))}</td><td><strong>{money(Number(plant.potential_savings))}</strong></td></tr>)}</tbody></table></div></div><div className="executive-table-panel"><div className="section-title"><div><span className="eyebrow">COMPONENT VALUE</span><h2>Leading components</h2></div></div><div className="table-wrap"><table><thead><tr><th>Component</th><th>Variance</th><th>Confidence</th><th>Savings</th></tr></thead><tbody>{detail.components.slice(0, 8).map(component => <tr key={component.component_id}><td><Link className="product-component-link" to={`/executive/components/${component.component_id}`}><strong>{component.component_name}</strong><small>{component.category} · {component.opportunity_count} opportunities</small></Link></td><td className="metric-risk">{percent(Number(component.variance_percent))}</td><td>{percent(Number(component.confidence_score) * 100)}</td><td><strong>{money(Number(component.potential_savings))}</strong></td></tr>)}</tbody></table></div></div></section>
    </>}
  </main>;
}
