import { Link } from "react-router";

export default function FinanceAnalystPage() {
  return (
    <main>
      <h1>Finance Analyst</h1>

      <Link to="/finance-analyst/opportunity-shortlisting">
        Opportunity Shortlisting
      </Link>
    </main>
  );
}