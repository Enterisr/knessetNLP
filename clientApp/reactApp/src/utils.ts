export function resolveServerURI(address: string) {
  const isProduction = process.env.NODE_ENV === "production";
  if (isProduction) {
    return address;
  } else {
    return `http://localhost:3000${address}`;
  }
}

export interface SentimentInfo {
  label: string;
  className: string;
}

export function getSentimentInfo(sentiment: number | undefined): SentimentInfo {
  if (sentiment === undefined)
    return { label: "Neutral", className: "sentiment-neutral" };

  if (sentiment >= 3.5) return { label: "לא חבר כנסת", className: "" };
  if (sentiment >= 2.5)
    return { label: "מצוין", className: "sentiment-positive" };
  if (sentiment >= 2) return { label: "טוב", className: "sentiment-neutral" };
  if (sentiment >= 1.5)
    return { label: "יש מקום לשיפור", className: "sentiment-negative" };
  return { label: "מזעזע", className: "sentiment-very-negative" };
}
