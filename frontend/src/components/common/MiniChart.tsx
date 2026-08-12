export default function MiniChart({ data, actual, peer, label = "12-month trend" }: { data: Record<string, unknown>[]; actual: string; peer?: string; label?: string }) {
  if (!data.length) return <div className="empty">No trend data available.</div>;
  const vals = data.flatMap(d => [Number(d[actual]), peer ? Number(d[peer]) : Number(d[actual])]).filter(Number.isFinite); const min=Math.min(...vals)*.96,max=Math.max(...vals)*1.04, w=640,h=210;
  const points=(key:string)=>data.map((d,i)=>`${(i/(Math.max(data.length-1,1)))*(w-40)+20},${h-20-((Number(d[key])-min)/(max-min||1))*(h-45)}`).join(" ");
  return <div className="chart"><div className="chart-head"><b>{label}</b><span><i className="legend actual"/>Actual {peer && <><i className="legend peer"/>Peer benchmark</>}</span></div><svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={label}><line x1="20" y1={h-20} x2={w-20} y2={h-20} className="grid"/><polyline points={points(actual)} className="line actual-line"/>{peer&&<polyline points={points(peer)} className="line peer-line"/>}</svg><div className="chart-labels"><span>{String(data[0].period ?? "")}</span><span>{String(data[data.length-1].period ?? "")}</span></div></div>;
}
