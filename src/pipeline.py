"""Convenience entry point: CSV -> Parquet -> checks -> star schema -> PostgreSQL."""
import logging

from src.ingest import ingest
from src.quality import check_processed
from src.transform import build_star_schema
from src.load import load_to_postgres


def run() -> None:
    ingest()
    check_processed()
    build_star_schema()
    load_to_postgres()
    logging.getLogger(__name__).info("Pipeline completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()

