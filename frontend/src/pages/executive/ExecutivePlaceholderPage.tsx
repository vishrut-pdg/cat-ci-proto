import { Link, useLocation, useParams } from "react-router";

const copy: Record<string, [string, string]> = {
  components: ["Component brief", "Supplier, volume, tariff, and commercial evidence will appear here for the selected component."],
  opportunities: ["Opportunity brief", "This portfolio item is ready to connect to the existing assignment and investigation lifecycle in the workflow checkpoint."],
  reports: ["Executive report", "The canonical report API is available; branded PDF composition follows in the reporting checkpoint."],
  products: ["Product detail", "Product trend, cost drivers, and benchmark drill-down will appear here for the selected product."],
};

export default function ExecutivePlaceholderPage() {
  const location = useLocation();
  const params = useParams();
  const key = location.pathname.includes("/components/") ? "components"
      : location.pathname.includes("/opportunities/") ? "opportunities"
        : location.pathname.includes("/reports") ? "reports" : "products";
  const [title, detail] = copy[key];
  const selectedId = params.productId ?? params.componentId ?? params.opportunityId;
  return <main className="executive-page">
    <div className="executive-heading"><div><span className="eyebrow">EXECUTIVE GUIDANCE</span><h1>{title}</h1><p>{selectedId ? `Selected ID: ${selectedId}` : "Enterprise scope"}</p></div></div>
    <section className="executive-placeholder"><span>↗</span><h2>Analytical foundation connected</h2><p>{detail}</p><Link to={key === "products" ? "/executive/products" : "/executive"}>Back to portfolio</Link></section>
  </main>;
}
