import { useMemo } from "react";
import styles from "./MKList.module.css";
import type { MKUtterances } from "../../types";
import { getSentimentInfo } from "../../utils";
import UtteranceItem from "../UtteranceItem/UtteranceItem";
import defaultMkImage from "../../assets/default-mk.svg";
import SentimentTag from "../SentimentTag/SentimentTag";

interface MKListProps {
  mks: MKUtterances;
  onMKSelect: (mkName: string) => void;
  loading: boolean;
}

const MKList = ({ mks, onMKSelect, loading }: MKListProps) => {
  const sortedMkIds = useMemo(() => {
    const mkIds = Object.keys(mks);
    return mkIds.sort((a, b) => {
      const scoreA = mks[a]?.total_relevance_score || 0;
      const scoreB = mks[b]?.total_relevance_score || 0;
      return scoreB - scoreA; // Sort descending (highest score first)
    });
  }, [mks]);

  if (loading) {
    return (
      <div className={styles["mk-list-loading"]}>
        <div className={styles["spinner"]}></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (sortedMkIds.length === 0) {
    return (
      <div className={styles["mk-list-empty"]}>
        <p>No results found</p>
      </div>
    );
  }

  return (
    <ul className={styles["mk-list"]}>
      {sortedMkIds.map((mkID) => {
        const mkIDNum = parseInt(mkID);
        const mkData = mks[mkIDNum];
        const mkName = mks[mkIDNum]?.name;
        const photoUrl = mkData?.metadata?.PhotoURL || defaultMkImage;
        const party = mkData?.metadata?.FactionName || "";
        const sentiment = mkData?.metadata?.sentiment || undefined;
        const relevanceScore = mkData?.total_relevance_score || 0;

        if (relevanceScore === undefined) {
          console.warn(`MK ${mkID} missing relevance score:`, mkData);
        }
        if (sentiment === undefined) {
          console.warn(`MK ${mkID} missing sentiment:`, mkData);
        }

        const topUtterances = mkData.utterances.slice(0, 5);
        const sentimentInfo = getSentimentInfo(sentiment);

        return (
          <li
            key={mkID}
            className={styles["mk-list-item"]}
            onClick={() => onMKSelect(mkID)}
            style={{ cursor: "pointer" }}
          >
            <div className={styles["mk-list-item-content"]}>
              <div className={styles["mk-details"]}>
                <div className={styles["mk-photo-container"]}>
                  <img
                    src={photoUrl}
                    alt={`${mkName}`}
                    className={styles["mk-photo"]}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = defaultMkImage;
                    }}
                  />
                </div>
                <div>
                  <h3 className={styles["mk-list-item-title"]}>{mkName}</h3>
                  {party && (
                    <p className={styles["mk-list-item-party"]}>{party}</p>
                  )}
                  <p className={styles["mk-list-item-description"]}>
                    רלוונטיות לחיפוש:{" "}
                    {relevanceScore !== undefined
                      ? relevanceScore.toFixed(3)
                      : "N/A"}
                  </p>

                  <SentimentTag
                    sentiment={sentiment}
                    sentimentInfo={sentimentInfo}
                  />
                </div>
                {/* Utterances Preview */}
                <div className={styles["mk-utterances-preview"]}>
                  {topUtterances.map((utterance, index) => (
                    <UtteranceItem
                      key={index}
                      utterance={utterance}
                      showRelevanceScore={true}
                      maxLength={150}
                    />
                  ))}
                </div>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
};

export default MKList;
