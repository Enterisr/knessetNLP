import { useMemo, useState } from "react";
import styles from "./PartyDistributionBar.module.css";

interface StackedBarSegment {
  key: string;
  label: string;
  color: string;
  value: number;
  percentValue: number;
  percentLabel: string;
  valueLabel: string;
}

interface StackedBarProps {
  segments: StackedBarSegment[];
}

type TooltipAlignment = "start" | "center" | "end";

interface ComputedSegment extends StackedBarSegment {
  alignment: TooltipAlignment;
  index: number;
}

const EDGE_THRESHOLD = 0.15;

const StackedBar = ({ segments }: StackedBarProps) => {
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const computedSegments = useMemo<ComputedSegment[]>(() => {
    let cumulative = 0;

    return segments.map((segment, index) => {
      const widthRatio = segment.percentValue;
      const segmentCenter = cumulative + widthRatio / 2;
      cumulative += widthRatio;

      let alignment: TooltipAlignment = "center";

      if (segmentCenter < EDGE_THRESHOLD) {
        alignment = "start";
      } else if (segmentCenter > 1 - EDGE_THRESHOLD) {
        alignment = "end";
      }

      return { ...segment, alignment, index };
    });
  }, [segments]);

  const handleActivate = (key: string) => {
    setActiveKey(key);
  };

  const handleDeactivate = (key: string) => {
    setActiveKey((current) => (current === key ? null : current));
  };

  const handleToggle = (key: string) => {
    setActiveKey((current) => (current === key ? null : key));
  };

  return (
    <div
      className={styles.barWrapper}
      role="list"
      aria-label="Party distribution bar"
    >
      <div className={styles.barTrack}>
        {computedSegments.map((segment) => {
          const isActive = activeKey === segment.key;
          const tooltipClassName = `${styles.segmentTooltip} ${
            segment.alignment === "start"
              ? styles.segmentTooltipStart
              : segment.alignment === "end"
              ? styles.segmentTooltipEnd
              : ""
          }`;

          return (
            <div
              key={segment.key}
              role="listitem"
              tabIndex={0}
              className={styles.barSegment}
              style={{
                backgroundColor: segment.color,
                flexBasis: 0,
                flexGrow: segment.value,
                minWidth: segment.value > 0 ? 6 : 0,
              }}
              aria-label={`${segment.label}: ${segment.percentLabel} (${segment.valueLabel})`}
              onMouseEnter={() => handleActivate(segment.key)}
              onFocus={() => handleActivate(segment.key)}
              onMouseLeave={() => handleDeactivate(segment.key)}
              onBlur={() => handleDeactivate(segment.key)}
              onPointerDown={(event) => {
                if (
                  event.pointerType === "touch" ||
                  event.pointerType === "pen"
                ) {
                  handleToggle(segment.key);
                }
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  handleToggle(segment.key);
                }
              }}
            >
              <span className={styles.visuallyHidden}>
                {segment.label} {segment.percentLabel} ({segment.valueLabel})
              </span>
              {isActive && (
                <div className={tooltipClassName} role="tooltip">
                  <div className={styles.tooltipHeader}>
                    <span
                      className={styles.tooltipSwatch}
                      style={{ backgroundColor: segment.color }}
                      aria-hidden="true"
                    />
                    <span className={styles.tooltipName}>{segment.label}</span>
                  </div>
                  <div className={styles.tooltipMetrics}>
                    <span className={styles.tooltipPercent}>
                      {segment.percentLabel}
                    </span>
                    <span className={styles.tooltipValue}>
                      {segment.valueLabel}
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export type { StackedBarSegment };
export default StackedBar;
