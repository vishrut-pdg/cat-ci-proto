import { Link } from "react-router";

export default function HomePage() {
  return (
    <main>
      <h1>CAT Cost Intelligence</h1>

      <Link to="/finance-analyst">
        Finance Analyst
      </Link>
    </main>
  );
}