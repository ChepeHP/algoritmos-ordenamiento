"""Run the full experiment and save every result. Run from the project root:

    python -m section1_comparison.activity3_experiment.run_experiment
"""

import platform
import time
from pathlib import Path

from section1_comparison.activity3_experiment.experiment import (
    COUNT_REPETITIONS,
    COUNT_SIZES,
    DEFAULT_REPETITIONS,
    DEFAULT_SIZES,
    GENERATORS,
    growth_fits,
    run_experiment,
    run_operation_counts,
    summarize,
    write_csv,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "section3_deliverables" / "data"


def main():
    configs = list(GENERATORS)
    started = time.perf_counter()

    def progress(done, total, name, config, n):
        print(f"[{done}/{total}] {name} {config} n={n} ({time.perf_counter() - started:.0f}s)", flush=True)

    raw = run_experiment(DEFAULT_SIZES, DEFAULT_REPETITIONS, configs, on_progress=progress)
    write_csv(DATA_DIR / "timings_raw.csv", raw)
    summary = summarize(raw)
    write_csv(DATA_DIR / "timings_summary.csv", summary)
    write_csv(DATA_DIR / "growth_fits.csv", growth_fits(summary))

    print("Counting operations...", flush=True)
    write_csv(DATA_DIR / "operation_counts.csv", run_operation_counts(COUNT_SIZES, COUNT_REPETITIONS, configs))

    (DATA_DIR / "environment.txt").write_text(
        f"python={platform.python_version()}\n"
        f"implementation={platform.python_implementation()}\n"
        f"machine={platform.machine()}\n"
        f"system={platform.system()} {platform.release()}\n"
        f"processor={platform.processor()}\n"
        f"sizes={DEFAULT_SIZES}\nrepetitions={DEFAULT_REPETITIONS}\n"
        f"count_sizes={COUNT_SIZES}\ncount_repetitions={COUNT_REPETITIONS}\nseed=42\n"
        f"total_seconds={time.perf_counter() - started:.0f}\n",
        encoding="utf-8",
    )
    print(f"Done in {time.perf_counter() - started:.0f}s. Results in {DATA_DIR}")


if __name__ == "__main__":
    main()
