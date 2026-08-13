import { useState } from "react";
import { Navigate, useNavigate } from "react-router";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { user, login } = useAuth(); const navigate = useNavigate();
  const [id, setId] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  if (user) return <Navigate to={user.role === "FINANCE_ANALYST" ? "/finance-analyst" : "/investigation-expert"} replace />;
  async function submit(e: React.FormEvent) { e.preventDefault(); setBusy(true); setError(""); try { const u = await login(id, password); navigate(u.role === "FINANCE_ANALYST" ? "/finance-analyst" : "/investigation-expert"); } catch (err) { setError(err instanceof Error ? err.message : "Login failed"); } finally { setBusy(false); } }
  return <main className="login-page"><section className="login-brand"><div className="logo login-logo"><div className="logo__cat">CAT</div><div className="logo__divider"/><div className="logo__text">Cost<br/>Intelligence Platform</div></div><p>COST INTELLIGENCE</p><h1>Turn cost variance into measurable value.</h1><p className="muted-light">A single evidence workspace for opportunity prioritization, investigation, and action.</p></section>
    <section className="login-panel"><form className="login-card" onSubmit={submit}><span className="eyebrow">CAT COST INTELLIGENCE</span><h2>Welcome back</h2><p className="muted">Sign in to your Cost Intelligence workspace.</p>
      <label>Username<input autoComplete="username" value={id} onChange={e => setId(e.target.value)} placeholder="Enter your username" required /></label>
      <label>Password<input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" required /></label>{error && <div className="error-box">{error}</div>}
      <button className="primary wide" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button><small>Secure access · Authorized users only</small></form></section></main>;
}
