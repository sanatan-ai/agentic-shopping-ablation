from __future__ import annotations

import logging
import sys

from src.preprocessing.config import PipelineConfig
from src.preprocessing.pipeline import run_pipeline


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg = PipelineConfig()
    try:
        run_pipeline(cfg)
    except Exception:
        logging.exception("Pipeline failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())