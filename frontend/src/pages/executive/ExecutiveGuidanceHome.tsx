import { useEffect, useState } from "react";
import { Link } from "react-router";
import ExecutiveFilters from "../../components/executive/ExecutiveFilters";
import { ExecutiveError, ExecutiveLoading } from "../../components/executive/ExecutiveState";
import { asOf, money, percent } from "../../components/executive/executiveFormat";
import { askExecutiveKatty, downloadExecutiveReport, generateExecutiveReport, getExecutiveSummary, getQuickWins, type ExecutiveFilters as Filters } from "../../services/executive";
import type { ExecutiveSummary, GeneratedExecutiveReport, QuickWin } from "../../types/executive";

const questions = [
  "Which are the top 5 products by savings opportunity?",
  "Where is the greatest aggregate value concentrated?",
  "Which products need a decision this quarter?",
  "What are the fastest savings actions?",
];

interface ChatMessage { role: "user" | "assistant"; content: string }

function AssistantText({ text }: { text: string }) {
  const inline = (value: string) => value.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((part, index) => part.startsWith("**") ? <strong key={index}>{part.slice(2, -2)}</strong> : part);
  return <div className="executive-answer-text">{text.split("\n").filter(Boolean).map((line, index) => line.startsWith("## ") ? <h3 key={index}>{line.slice(3)}</h3> : line.startsWith("- ") ? <div className="executive-answer-bullet" key={index}><i/> <span>{inline(line.slice(2))}</span></div> : <p key={index}>{inline(line)}</p>)}</div>;
}

export default function ExecutiveGuidanceHome() {
  const [filters, setFilters] = useState<Filters>({ period: "FY26", scope: "enterprise" });
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [wins, setWins] = useState<QuickWin[]>([]);
  const [error, setError] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string>();
  const [provider, setProvider] = useState<"vertex_ai" | "local_grounded_fallback" | "error" | "ready">("ready");
  const [providerNote, setProviderNote] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [report, setReport] = useState<GeneratedExecutiveReport | null>(null);
  const [reportBusy, setReportBusy] = useState(false);
  const [reportError, setReportError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([getExecutiveSummary(filters), getQuickWins(filters)])
      .then(([nextSummary, nextWins]) => {
        if (active) { setSummary(nextSummary); setWins(nextWins.items); setError(""); }
      })
      .catch(err => active && setError(err instanceof Error ? err.message : "Request failed"));
    return () => { active = false; };
  }, [filters]);

  async function send(value = question) {
    const clean = value.trim();
    if (!clean || chatBusy) return;
    setQuestion("");
    setMessages(current => [...current, { role: "user", content: clean }]);
    setChatBusy(true);
    setProviderNote("");
    try {
      const reply = await askExecutiveKatty(clean, sessionId, filters);
      setMessages(current => [...current, { role: "assistant", content: reply.answer }]);
      setSessionId(reply.session_id);
      setProvider(reply.provider);
      setProviderNote(reply.provider_note ?? "");
    } catch (chatError) {
      setProvider("error");
      setMessages(current => [...current, { role: "assistant", content: chatError instanceof Error ? `I couldn't complete that request: ${chatError.message}` : "I couldn't reach the assistant service." }]);
    } finally {
      setChatBusy(false);
    }
  }

  async function createReport() {
    setReportBusy(true); setReportError("");
    try { setReport(await generateExecutiveReport(filters)); }
    catch (requestError) { setReportError(requestError instanceof Error ? requestError.message : "Report generation failed"); }
    finally { setReportBusy(false); }
  }

  async function downloadReport() {
    if (!report) return;
    try { await downloadExecutiveReport(report); }
    catch (requestError) { setReportError(requestError instanceof Error ? requestError.message : "Report download failed"); }
  }

  const cards = summary ? [
    ["Top plant", summary.top_plant, "/executive/plants"],
    ["Top category", summary.top_category, "/executive/categories"],
    ["Top product", summary.top_product, summary.top_product ? `/executive/products/${summary.top_product.id}` : "/executive/products"],
    ["Top component", summary.top_component, summary.top_component ? `/executive/components/${summary.top_component.id}` : "/executive/categories"],
  ] as const : [];

  return <main className="executive-page">
    <div className="executive-heading">
      <div><span className="eyebrow">EXECUTIVE GUIDANCE</span><h1>Where should we focus next?</h1><p>A portfolio view of validated cost opportunities, benchmark gaps, and actions.</p></div>
      <ExecutiveFilters value={filters} onChange={setFilters} asOfDate={summary?.as_of_date}/>
    </div>
    {error ? <ExecutiveError message={error}/> : !summary ? <ExecutiveLoading/> : <>
      <section className="executive-assistant-card">
        <header>
          <div className="executive-assistant-title"><span>✦</span><div><h2>Ask Katty</h2><p>Executive cost guidance across products, plants, categories and components</p></div></div>
          <div className="executive-assistant-meta"><span className={`assistant-status ${provider}`}>{provider === "vertex_ai" ? "Vertex AI" : provider === "local_grounded_fallback" ? "Grounded demo" : provider === "error" ? "Unavailable" : "Beta"}</span><strong>{money(summary.total_potential_savings)}</strong><small>{summary.opportunity_count} opportunities</small></div>
        </header>
        {messages.length > 0 && <div className="executive-chat-thread" aria-live="polite">{messages.map((message, index) => <article className={message.role} key={`${message.role}-${index}`}><small>{message.role === "user" ? "You" : "Katty"}</small>{message.role === "assistant" ? <AssistantText text={message.content}/> : <p>{message.content}</p>}</article>)}{chatBusy && <article className="assistant typing"><small>Katty</small><div><i/><i/><i/></div></article>}</div>}
        {messages.length === 0 && <div className="executive-question-grid">{questions.map(item => <button key={item} disabled={chatBusy} onClick={() => send(item)}>{item}<span>→</span></button>)}</div>}
        <div className="executive-chat-input"><input value={question} disabled={chatBusy} onChange={event => setQuestion(event.target.value)} onKeyDown={event => { if (event.key === "Enter") { event.preventDefault(); send(); } }} placeholder={chatBusy ? "Katty is analyzing portfolio evidence…" : "Ask Katty for executive guidance…"}/><button disabled={chatBusy || !question.trim()} onClick={() => send()}>{chatBusy ? "Working…" : "Send"}</button></div>
        <footer><span>Answers use structured portfolio evidence as of {asOf(summary.as_of_date)}.</span>{providerNote && <span>{providerNote}; using the deterministic grounded response.</span>}{messages.length > 0 && <button onClick={() => { setMessages([]); setSessionId(undefined); setProvider("ready"); setProviderNote(""); }}>New conversation</button>}</footer>
      </section>
      <section>
        <div className="section-title"><div><span className="eyebrow">TOP PRIORITIES</span><h2>Value concentration at a glance</h2></div><span>Ranked by backend policy</span></div>
        <div className="priority-grid">{cards.map(([label, entity, link]) => <Link to={link} className="priority-card" key={label}><span>{label}</span><h3>{entity?.name ?? "Not available"}</h3><strong>{entity ? money(Number(entity.potential_savings)) : "—"}</strong><p>{entity ? `${percent(Number(entity.variance_percent))} weighted variance · ${entity.opportunity_count} opportunities` : "No attributed opportunities"}</p><b>Explore <i>→</i></b></Link>)}</div>
      </section>
      <section className="quick-wins-panel">
        <div className="section-title"><div><span className="eyebrow">RECOMMENDED QUICK WINS</span><h2>Actions with value and executable evidence</h2></div></div>
        <div className="table-wrap"><table><thead><tr><th>Rank</th><th>Opportunity</th><th>Potential savings</th><th>Ease</th><th>Confidence</th><th>Urgency</th><th>Why now</th><th/></tr></thead><tbody>{wins.map(win => <tr key={win.opportunity_id}><td><b className="rank-circle">{win.rank}</b></td><td><strong>{win.title}</strong><small>{win.opportunity_id}</small></td><td><strong>{money(Number(win.potential_savings))}</strong></td><td><span className={`executive-chip ${win.ease.toLowerCase()}`}>{win.ease}</span></td><td>{Math.round(Number(win.confidence) * 100)}%</td><td><span className={`executive-chip ${win.urgency.toLowerCase()}`}>{win.urgency}</span></td><td className="why-now">{win.why_now}</td><td><Link to={`/executive/opportunities/${win.opportunity_id}`}>Open brief</Link></td></tr>)}</tbody></table></div>
      </section>
      <section className="executive-report-generator">
        <header><span>▤</span><div><small>AI-GROUNDED REPORTING</small><h2>Generate executive report</h2><p>Create a concise leadership report from the latest PostgreSQL evidence and recommended actions.</p></div>{report && <b className={`assistant-status ${report.provider}`}>{report.provider === "vertex_ai" ? "Vertex AI" : "Grounded demo"}</b>}</header>
        {!report ? <div className="report-generator-action"><div><span><small>REPORTING PERIOD</small><b>{filters.period ?? "FY26"}</b></span><span><small>SCOPE</small><b>Enterprise</b></span></div><button disabled={reportBusy} onClick={createReport}>{reportBusy ? "Katty is generating the report…" : "Generate AI report"}</button>{reportError && <p>{reportError}</p>}</div> : <div className="generated-report"><div className="generated-report-meta"><span>Generated from data as of <b>{asOf(report.as_of_date)}</b></span><span>Stored in MinIO · {report.provider_note ? "deterministic narrative used" : `${report.model} narrative`}</span></div><AssistantText text={report.narrative}/>{reportError && <p className="report-download-error">{reportError}</p>}<footer><button className="secondary" onClick={() => { setReport(null); setReportError(""); }}>Generate again</button><button onClick={downloadReport}>Download PDF</button></footer></div>}
      </section>
    </>}
  </main>;
}
