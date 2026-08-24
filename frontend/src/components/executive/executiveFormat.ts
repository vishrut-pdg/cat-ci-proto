export const money = (value: number, compact = true) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: compact ? 1 : 0,
  notation: compact ? "compact" : "standard",
}).format(value);

export const percent = (value: number) => `${Number(value).toFixed(1)}%`;
