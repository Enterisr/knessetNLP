import "./SentimentTag.css";
import type { SentimentInfo } from "../../utils";

interface SentimentTagProps {
  sentiment?: number;
  sentimentInfo: SentimentInfo;
}

const SentimentTag = ({ sentimentInfo, sentiment }: SentimentTagProps) => {
  return (
    <div
      className={`st-sentiment ${sentimentInfo.className}`}
      title="הציון מורכב מממוצע ניתוח סנטימנט של 500 אמירות אקראיות של חבר הכנסת"
    >
      <span className="st-label">דרך ארץ: {sentimentInfo.label}</span>
      {sentiment !== undefined && (
        <span className="st-score"> ({sentiment.toFixed(2)})</span>
      )}
    </div>
  );
};

export default SentimentTag;
