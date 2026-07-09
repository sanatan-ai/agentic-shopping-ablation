"""Query CloudWatch for Bedrock latency across the full experiment window.

Run this AFTER the full experiment completes. Pulls the AWS/Bedrock
InvocationLatency metric for the experiment's time window, summarises,
and writes a CSV.

Usage:
    uv run python scripts/query_experiment_latency.py --start "2026-06-20 09:00" --end "2026-06-20 21:00"

The start/end times define the analysis window. If omitted, defaults to
the last 24 hours (usually a superset of one full-experiment run).
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3

REGION = "us-east-1"
MODEL_ID = "us.meta.llama3-1-70b-instruct-v1:0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CSV = PROJECT_ROOT / "data" / "results" / "cloudwatch_latency_full_experiment.csv"


def parse_time(s: str) -> datetime:
    """Parse a 'YYYY-MM-DD HH:MM' string as UTC."""
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=timezone.utc)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("query_experiment_latency")

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, default=None,
                        help="Start time (UTC) as 'YYYY-MM-DD HH:MM'. Defaults to 24h ago.")
    parser.add_argument("--end", type=str, default=None,
                        help="End time (UTC) as 'YYYY-MM-DD HH:MM'. Defaults to now.")
    parser.add_argument("--period-minutes", type=int, default=5,
                        help="Aggregation period in minutes (default: 5)")
    args = parser.parse_args()

    end_time = parse_time(args.end) if args.end else datetime.now(timezone.utc)
    start_time = parse_time(args.start) if args.start else end_time - timedelta(hours=24)

    log.info("Querying CloudWatch InvocationLatency for Bedrock")
    log.info("  Region: %s", REGION)
    log.info("  Model:  %s", MODEL_ID)
    log.info("  Window: %s → %s", start_time.isoformat(), end_time.isoformat())

    client = boto3.client("cloudwatch", region_name=REGION)

    response = client.get_metric_statistics(
        Namespace="AWS/Bedrock",
        MetricName="InvocationLatency",
        Dimensions=[{"Name": "ModelId", "Value": MODEL_ID}],
        StartTime=start_time,
        EndTime=end_time,
        Period=args.period_minutes * 60,
        Statistics=["Average", "Minimum", "Maximum", "SampleCount"],
    )

    datapoints = sorted(response.get("Datapoints", []), key=lambda d: d["Timestamp"])

    if not datapoints:
        log.warning("No datapoints found in window. Note: CloudWatch propagation delay is 2-5 min.")
        return 1

    # Aggregate stats
    total_calls = sum(int(d["SampleCount"]) for d in datapoints)
    weighted_avg = sum(d["Average"] * d["SampleCount"] for d in datapoints) / total_calls
    overall_min = min(d["Minimum"] for d in datapoints)
    overall_max = max(d["Maximum"] for d in datapoints)

    log.info("=" * 70)
    log.info("Summary:")
    log.info("  Datapoints:      %d (%d-minute buckets)", len(datapoints), args.period_minutes)
    log.info("  Total calls:     %d", total_calls)
    log.info("  Mean latency:    %.1f ms", weighted_avg)
    log.info("  Min latency:     %.1f ms", overall_min)
    log.info("  Max latency:     %.1f ms", overall_max)
    log.info("=" * 70)

    # Write CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_utc", "sample_count", "min_ms", "avg_ms", "max_ms"])
        for d in datapoints:
            writer.writerow([
                d["Timestamp"].isoformat(),
                int(d["SampleCount"]),
                round(d["Minimum"], 1),
                round(d["Average"], 1),
                round(d["Maximum"], 1),
            ])

    log.info("Wrote %d rows to %s", len(datapoints), OUTPUT_CSV)
    return 0


if __name__ == "__main__":
    sys.exit(main())