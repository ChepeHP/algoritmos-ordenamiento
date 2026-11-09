"""Load and save experiment results, including the chart images. Run from the project root
to rebuild the charts from the saved data:

    python -m section1_comparison.activity4_results.results_io
"""

import csv
from pathlib import Path

from matplotlib.figure import Figure

import theme
from section1_comparison.activity3_experiment.experiment import growth_fits, summarize, write_csv
from section1_comparison.activity4_results.charts import CHARTS, apply_chart_style

DELIVERABLES = Path(__file__).resolve().parents[2] / "section3_deliverables"
TEXT_FIELDS = {"algorithm", "config"}


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key, value in row.items():
            if key not in TEXT_FIELDS:
                row[key] = float(value) if "." in value or "e" in value else int(value)
    return rows


def load_saved(folder):
    """Return the saved results, or None if the timing file does not exist."""
    folder = Path(folder)
    raw_path = folder / "timings_raw.csv"
    if not raw_path.exists():
        return None
    raw = _read_csv(raw_path)
    summary = summarize(raw)
    operations_path = folder / "operation_counts.csv"
    return {
        "raw": raw,
        "summary": summary,
        "fits": growth_fits(summary),
        "operations": _read_csv(operations_path) if operations_path.exists() else [],
    }


def save_data(folder, results):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    write_csv(folder / "timings_raw.csv", results["raw"])
    write_csv(folder / "timings_summary.csv", results["summary"])
    if results["fits"]:
        write_csv(folder / "growth_fits.csv", results["fits"])
    if results["operations"]:
        write_csv(folder / "operation_counts.csv", results["operations"])


def save_charts(folder, results):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    apply_chart_style()
    saved = []
    for title, draw, needs, name in CHARTS:
        if not results[needs]:
            continue
        figure = Figure(figsize=(11, 7), dpi=160)
        draw(figure, results)
        figure.suptitle(title, x=0.075, ha="left", fontsize=13, fontweight="bold", color=theme.INK)
        figure.savefig(folder / f"{name}.png")
        saved.append(name)
    return saved


if __name__ == "__main__":
    data = load_saved(DELIVERABLES / "data")
    print(save_charts(DELIVERABLES / "charts", data))
