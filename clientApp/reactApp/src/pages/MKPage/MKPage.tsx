import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getSentimentInfo } from "../../utils";
import type { Utterance, MKMetadata } from "../../types";
import UtteranceItem from "../../components/UtteranceItem/UtteranceItem";
import { useSearch } from "../../hooks/useSearch";
import styles from "./MKPage.module.css";
import defaultMkImage from "../../assets/default-mk.svg";
import SentimentTag from "../../components/SentimentTag/SentimentTag";

const MKPage = () => {
  const { mkName: mkId, query } = useParams<{
    mkName: string;
    query: string;
  }>();
  const [utterances, setUtterances] = useState<Utterance[]>([]);
  const [metadata, setMetadata] = useState<MKMetadata | null>(null);
  const { searchResults, currentQuery, loading, fetchFromServer } = useSearch();

  useEffect(() => {
    if (mkId && query) {
      if (currentQuery !== query) {
        fetchFromServer(query);
      } else if (searchResults && mkId) {
        const decodedMkName = decodeURIComponent(mkId);
        const mkData = searchResults[decodedMkName];

        if (mkData) {
          setUtterances(mkData.utterances || []);
          setMetadata(mkData.metadata || null);
        } else {
          setUtterances([]);
          setMetadata(null);
        }
      }
    }
  }, [mkId, query, searchResults, currentQuery, fetchFromServer]);

  if (loading) {
    return (
      <main className="app-main">
        <div className={styles["mk-page-loading"]}>
          <div className={styles["spinner"]}></div>
          <p>טוען...</p>
        </div>
      </main>
    );
  }

  const mkName = metadata?.FirstName + " " + metadata?.LastName;
  const photoUrl = metadata?.PhotoURL || defaultMkImage;
  const factionName = metadata?.FactionName || "";
  const sentimentInfo = getSentimentInfo(metadata?.sentiment);

  return (
    <main className="app-main">
      <div className={styles["mk-page"]}>
        <div className={styles["mk-page-header"]}>
          <Link
            to={`/search/${encodeURIComponent(query!)}`}
            className={styles["back-button"]}
          >
            ️️➡️חזרה לרשימה כללית
          </Link>
          <div className={styles["mk-profile"]}>
            <div className={styles["mk-photo-container"]}>
              <img
                src={photoUrl}
                alt={mkId}
                className={styles["mk-photo"]}
                onError={(e) => {
                  (e.target as HTMLImageElement).src = defaultMkImage;
                }}
              />
            </div>
            <div className={styles["mk-details"]}>
              <h1 className={styles["mk-name"]}>{mkName}</h1>
              {factionName && (
                <span className={styles["mk-faction"]}>{factionName}</span>
              )}
              <div
                className={`${styles["mk-stat"]} ${styles["mk-stat-label"]} ${styles["mk-email"]}`}
              >
                <a href={`mailto:${metadata?.Email}`}>{metadata?.Email}</a>
              </div>
              <div className={styles["mk-stats"]}>
                <div className={styles["mk-stat"]}>
                  <span className={styles["mk-stat-label"]}>
                    התבטאויות: &nbsp;
                  </span>
                  <span className={styles["mk-stat-value"]}>
                    {utterances.length}
                  </span>
                </div>
                <div className={styles["mk-stat"]}>
                  <SentimentTag
                    sentiment={metadata?.sentiment}
                    sentimentInfo={sentimentInfo}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className={styles["mk-utterances"]}>
          <h2 className={styles["mk-utterances-title"]}>
            התבטאויות על "{decodeURIComponent(query!)}"
          </h2>
          <div className={styles["utterances-container"]}>
            {utterances.map((utterance, index) => (
              <UtteranceItem
                key={index}
                utterance={utterance}
                showRelevanceScore={true}
                maxLength={300}
              />
            ))}
          </div>
        </div>
      </div>
    </main>
  );
};

export default MKPage;
