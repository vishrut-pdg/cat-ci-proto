export function ExecutiveLoading() { return <div className="executive-state"><i/>Loading executive intelligence…</div>; }
export function ExecutiveError({ message }: { message: string }) { return <div className="executive-state error-box">Unable to load executive data: {message}</div>; }
