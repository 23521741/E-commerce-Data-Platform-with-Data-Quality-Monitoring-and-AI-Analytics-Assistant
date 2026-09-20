"""Read immutable raw CSVs and produce normalized Parquet files."""
import argparse
import logging
import re
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR, REQUIRED_TABLES, TABLE_SCHEMAS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def snake_case(name: str) -> str:
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def normalize_dataframe(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Normalize header/types without changing the source CSV."""
    result = df.copy()
    result.columns = [snake_case(column) for column in result.columns]
    schema = TABLE_SCHEMAS.get(table, {})
    for column in schema.get("dates", []):
        if column in result:
            result[column] = pd.to_datetime(result[column], errors="coerce", utc=True).dt.tz_localize(None)
    for column in schema.get("integers", []):
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="coerce").astype("Int64")
    for column in schema.get("numbers", []):
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result.sort_index(axis=1)


def ingest(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> dict[str, int]:
    processed_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for table in REQUIRED_TABLES:
        source = raw_dir / f"{table}.csv"
        if not source.exists():
            raise FileNotFoundError(f"Missing required raw file: {source}")
        frame = normalize_dataframe(pd.read_csv(source), table)
        target = processed_dir / f"{table}.parquet"
        # Overwriting only the generated artifact makes reruns deterministic and leaves raw data untouched.
        frame.to_parquet(target, index=False, engine="pyarrow")
        counts[table] = len(frame)
        logger.info("%s: read=%d wrote=%d -> %s", table, len(frame), len(frame), target)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args()
    ingest(args.raw_dir, args.processed_dir)

