import type { ExecutiveFilters as Filters } from "../../services/executive";

export default function ExecutiveFilters({ value, onChange, asOfDate }: { value: Filters; onChange: (next: Filters) => void; asOfDate?: string }) {
  return <div className="executive-filters">
    <label>Reporting period<select value={value.period ?? "FY26"} onChange={event => onChange({ ...value, period: event.target.value })}><option>FY26</option><option>FY25</option></select></label>
    <label>Scope<select value={value.scope ?? "enterprise"} onChange={event => onChange({ ...value, scope: event.target.value })}><option value="enterprise">Enterprise</option></select></label>
    {asOfDate && <span>Data as of <b>{new Date(`${asOfDate}T00:00:00`).toLocaleDateString(undefined, { dateStyle: "medium" })}</b></span>}
  </div>;
}
