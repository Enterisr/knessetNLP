import styles from "./UtteranceItem.module.css";
import type { Utterance } from "../../types";

interface UtteranceItemProps {
  utterance: Utterance;
  showRelevanceScore?: boolean;
  maxLength?: number;
}

const UtteranceItem = ({
  utterance,
  showRelevanceScore = true,
  maxLength = 150,
}: UtteranceItemProps) => {
  return (
    <div className={styles["utterance-preview"]}>
      <div className={styles["utterance-scores"]}>
        {showRelevanceScore && utterance.relevance_score !== undefined && (
          <span className={styles["relevance-score"]}>
            Score: {utterance.relevance_score.toFixed(3)}
          </span>
        )}
        {(utterance.committee || utterance.subject) && (
          <div
            className={`${styles["protocol-info"]} ${
              utterance.src ? styles["clickable"] : ""
            }`}
            onClick={
              utterance.src
                ? () =>
                    window.open(utterance.src, "_blank", "noopener,noreferrer")
                : undefined
            }
            title={utterance.src ? "לחץ לפתיחת הפרוטוקול המלא" : undefined}
          >
            <div className={styles["utterance-doc"]}>
              <span className={styles["document-icon"]}>📄 </span>
              {utterance.committee && ` מתוך: ${utterance.committee}`}
              {utterance.subject && ` | נושא: ${utterance.subject}`}
            </div>
          </div>
        )}
      </div>
      <p className={styles["utterance-text"]}>
        {utterance.text.length > maxLength
          ? utterance.text.substring(0, maxLength) + "..."
          : utterance.text}
      </p>
    </div>
  );
};

export default UtteranceItem;
