"""
Report generator for filtered utterances analysis and summary creation.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from utils.logger_config import get_logger

logger = get_logger(__name__)


class FilterReportGenerator:
    """Handles generation of filtered utterance reports and summaries."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def generate_summary_report(self, filtered_df, threshold: float, scores: np.ndarray) -> None:
        """Generate a comprehensive summary report of filtered utterances."""
        summary_path = self.project_root / f"filtered_summary_{threshold}.txt"

        with open(summary_path, 'w', encoding='utf-8') as f:
            self._write_header(f, threshold, len(filtered_df), scores)
            self._write_top_scoring_section(f, filtered_df)
            self._write_lowest_scoring_section(f, filtered_df)
            self._write_random_sample_section(f, filtered_df)

        logger.info("Saved summary to %s", summary_path)

    def _write_header(self, f, threshold: float, total_count: int, scores: np.ndarray) -> None:
        """Write the header section of the report."""
        f.write(f"Filtered Out Utterances Summary (threshold: {threshold})\n")
        f.write(f"{'='*50}\n")
        f.write(f"Total filtered: {total_count}\n")
        f.write(f"Score range: {scores.min():.4f} - {scores.max():.4f}\n")
        f.write(f"Mean score: {scores.mean():.4f}\n\n")

    def _write_top_scoring_section(self, f, filtered_df) -> None:
        """Write the top 20 highest scoring filtered utterances."""
        top_20_highest = filtered_df.head(20)
        f.write("Top 20 Highest Scoring Filtered Utterances:\n")
        f.write("-" * 50 + "\n")

        for idx, (_, row) in enumerate(top_20_highest.iterrows(), 1):
            self._write_utterance_entry(f, idx, row, numbered=True)

    def _write_lowest_scoring_section(self, f, filtered_df) -> None:
        """Write the top 5 lowest scoring filtered utterances."""
        lowest_5 = filtered_df.tail(5).sort_values('importance_score')
        f.write("Top 5 Lowest Scoring Filtered Utterances:\n")
        f.write("-" * 45 + "\n")

        for idx, (_, row) in enumerate(lowest_5.iterrows(), 1):
            self._write_utterance_entry(f, idx, row, numbered=True)

    def _write_random_sample_section(self, f, filtered_df) -> None:
        """Write random samples from the middle range."""
        if len(filtered_df) <= 30:
            return

        middle_start = len(filtered_df) // 3
        middle_end = 2 * len(filtered_df) // 3
        sample_size = min(5, middle_end - middle_start)
        random_sample = filtered_df.iloc[middle_start:middle_end].sample(
            sample_size)

        f.write("Random Sample from Middle Range:\n")
        f.write("-" * 35 + "\n")

        for idx, (_, row) in enumerate(random_sample.iterrows(), 1):
            self._write_utterance_entry(f, idx, row, numbered=True)

    def _write_utterance_entry(self, f, idx: int, row, numbered: bool = False) -> None:
        """Write a single utterance entry to the file."""
        prefix = f"{idx:2d}. " if numbered else f"{idx}. "
        indent = "    " if numbered else "   "

        f.write(f"{prefix}Score: {row['importance_score']:.4f}\n")
        f.write(f"{indent}Text: {row['text'][:80]}...\n")
        f.write(f"{indent}Committee: {row.get('committee', 'N/A')}\n")
        f.write(f"{indent}MK: {row.get('mk', 'N/A')}\n\n")

    def validate_filtered_json(self, threshold: float) -> None:
        """Validate and display info about the filtered JSON file."""
        output_path = self.project_root / \
            f"filtered_out_utterances_{threshold}.json"

        if not output_path.exists():
            logger.warning("Filtered file not found: %s", output_path)
            return

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info("Loaded %d filtered utterances from %s",
                        len(data), output_path)

            # Check for duplicates
            duplicates = self._check_duplicates(data)
            if duplicates > 0:
                logger.warning(
                    "Found %d duplicate utterances in filtered file", duplicates)

            # Show score statistics
            self._log_score_statistics(data)
            self._log_sample_entries(data)

        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.error("Error validating filtered JSON: %s", e)

    def _check_duplicates(self, data: List[Dict[str, Any]]) -> int:
        """Check for duplicate utterances in the data."""
        unique_ids = set()
        duplicates = 0

        for item in data:
            utter_id = item.get('utter_id', '')
            if utter_id in unique_ids:
                duplicates += 1
            else:
                unique_ids.add(utter_id)

        return duplicates

    def _log_score_statistics(self, data: List[Dict[str, Any]]) -> None:
        """Log score statistics for the filtered data."""
        scores = [item.get('importance_score', 0) for item in data]
        if scores:
            logger.info(
                "Score statistics - Min: %.4f, Max: %.4f, Mean: %.4f",
                min(scores), max(scores), np.mean(scores)
            )

    def _log_sample_entries(self, data: List[Dict[str, Any]]) -> None:
        """Log sample entries from the filtered data."""
        logger.info("First 3 filtered utterances:")
        for i, item in enumerate(data[:3]):
            score = item.get('importance_score', 'N/A')
            text = item.get('text', '')[:80]
            logger.info("  %d. Score: %.4f, Text: %s...", i+1, score, text)

    def get_filtered_stats(self, threshold: float) -> Dict[str, Any]:
        """Get statistics about filtered utterances."""
        output_path = self.project_root / \
            f"filtered_out_utterances_{threshold}.json"

        if not output_path.exists():
            return {"error": "Filtered file not found"}

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            scores = [item.get('importance_score', 0) for item in data]

            return {
                "total_filtered": len(data),
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "mean_score": np.mean(scores) if scores else 0,
                "threshold": threshold
            }

        except (json.JSONDecodeError, IOError, KeyError) as e:
            return {"error": str(e)}
