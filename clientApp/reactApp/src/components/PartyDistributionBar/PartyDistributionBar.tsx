import { useMemo } from "react";
import type { MKUtterances } from "../../types";
import styles from "./PartyDistributionBar.module.css";
import StackedBar, { type StackedBarSegment } from "./StackedBar";

interface PartyDistributionBarProps {
  mks: MKUtterances;
}

interface PartyDistributionDatum {
  key: string;
  name: string;
  value: number;
  color: string;
}

const COLOR_PALETTE = [
  "#3b82f6",
  "#ef4444",
  "#10b981",
  "#f59e0b",
  "#8b5cf6",
  "#0ea5e9",
  "#ec4899",
  "#14b8a6",
  "#f97316",
  "#6366f1",
];

const formatPercentage = (value: number, total: number) => {
  if (!total) {
    return "0%";
  }
  const percent = (value / total) * 100;
  const digits = percent >= 10 ? 0 : 1;
  return `${percent.toFixed(digits)}%`;
};

const PartyDistributionBar = ({ mks }: PartyDistributionBarProps) => {
  const { parties, total } = useMemo(() => {
    const totals = new Map<string, number>();
    let aggregateTotal = 0;

    Object.values(mks).forEach((mk) => {
      const partyName =
        (mk.metadata?.FactionName ?? "Unknown").trim() || "Unknown";
      const relevance = mk.total_relevance_score;

      const fallbackUtteranceScore = mk.utterances.reduce((acc, utterance) => {
        return acc + (utterance.relevance_score ?? 0);
      }, 0);

      const contribution =
        typeof relevance === "number" && relevance > 0
          ? relevance
          : fallbackUtteranceScore > 0
          ? fallbackUtteranceScore
          : mk.utterances.length;

      if (contribution <= 0) {
        return;
      }

      aggregateTotal += contribution;
      totals.set(partyName, (totals.get(partyName) ?? 0) + contribution);
    });

    const items: PartyDistributionDatum[] = Array.from(totals.entries())
      .map(([name, value], index) => ({
        key: name,
        name,
        value,
        color: COLOR_PALETTE[index % COLOR_PALETTE.length],
      }))
      .sort((a, b) => b.value - a.value);

    return { parties: items, total: aggregateTotal };
  }, [mks]);

  const segments: StackedBarSegment[] = useMemo(() => {
    return parties.map((party) => {
      const percentValue = total > 0 ? party.value / total : 0;

      return {
        key: party.key,
        label: party.name,
        color: party.color,
        value: party.value,
        percentValue,
        percentLabel: formatPercentage(party.value, total),
        valueLabel: party.value.toLocaleString(undefined, {
          maximumFractionDigits: 1,
        }),
      } satisfies StackedBarSegment;
    });
  }, [parties, total]);

  if (segments.length === 0 || total <= 0) {
    return null;
  }

  return (
    <section
      className={styles.container}
      aria-label="Party involvement breakdown"
    >
      <h2 className={styles.title}>מעורבות לפי מפלגה </h2>
      <StackedBar segments={segments} />
      <ul className={styles.legend}>
        {parties.map((party) => (
          <li key={party.key} className={styles.legendItem}>
            <span
              className={styles.legendSwatch}
              style={{ backgroundColor: party.color }}
              aria-hidden="true"
            />
            <span className={styles.legendLabel}>{party.name}</span>
            <span className={styles.legendValue}>
              {formatPercentage(party.value, total)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default PartyDistributionBar;
