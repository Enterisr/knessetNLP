import styles from "./UtterancesList.module.css";
import type { DetailedUtterance } from "../../types/index";

interface UtterancesListProps {
  utterances: DetailedUtterance[];
  query: string;
  onBack: () => void;
  loading: boolean;
}

const UtterancesList = ({
  utterances,
  query,
  onBack,
  loading,
}: UtterancesListProps) => {
  const highlightQuery = (text: string, query: string) => {
    if (!query) return text;

    const regex = new RegExp(`(${query})`, "gi");
    const newText = text.replace(regex, "<mark>$1</mark>");
    return <div>{newText}</div>;
  };

  return (
    <div className={styles["utterances-list"]}>
      <div className={styles["utterances-header"]}>
        <button onClick={onBack} className={styles["back-button"]}>
          Back
        </button>
      </div>
      {loading ? (
        <div className={styles["loading"]}>Loading...</div>
      ) : (
        <div className={styles["utterances-content"]}>
          {utterances.map((utterance) => (
            <div key={utterance.id} className={styles["utterance-item"]}>
              <div className={styles["utterance-text"]}>
                {highlightQuery(utterance.text, query)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UtterancesList;
