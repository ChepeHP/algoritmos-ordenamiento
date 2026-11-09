"""Experimental comparison: datasets, timing, operation counts and growth fits."""

import csv
import gc
import math
import random
import sys
import time
from functools import lru_cache
from statistics import fmean, median, stdev

import numpy as np

from section1_comparison.activity2_implementation.algorithms import (
    _quicksort,
    bubble_sort,
    quicksort,
)

# The adversarial input drives recursion depth close to n/2.
sys.setrecursionlimit(200_000)

ALGORITHMS = {"Bubble Sort": bubble_sort, "Quicksort": quicksort}
DEFAULT_SIZES = [250, 500, 1000, 2000, 4000, 8000, 16000]
DEFAULT_REPETITIONS = 7
COUNT_SIZES = [250, 500, 1000, 2000, 4000]
COUNT_REPETITIONS = 3


@lru_cache(maxsize=None)
def median_of_three_killer(n):
    """Build a worst-case input with McIlroy's adversary (1999).

    Quicksort runs on items whose order is decided during the comparisons, always in
    the way that hurts the pivot choice most. The resulting order is then a fixed input
    that forces the same behaviour on the real, deterministic algorithm.
    """
    gas = n
    values = [gas] * n
    state = {"solid": 0, "candidate": 0}

    def freeze(x):
        values[x] = state["solid"]
        state["solid"] += 1

    def compare(x, y):
        if values[x] == gas and values[y] == gas:
            freeze(x if x == state["candidate"] else y)
        if values[x] == gas:
            state["candidate"] = x
        elif values[y] == gas:
            state["candidate"] = y
        return values[x] - values[y]

    class Item:
        def __init__(self, index):
            self.index = index

        def __lt__(self, other):
            return compare(self.index, other.index) < 0

        def __gt__(self, other):
            return compare(self.index, other.index) > 0

    quicksort([Item(i) for i in range(n)])
    return tuple(float(v) for v in values)


GENERATORS = {
    "random": lambda n, rng: [rng.uniform(-1e6, 1e6) for _ in range(n)],
    "random_int": lambda n, rng: [rng.randint(-1_000_000, 1_000_000) for _ in range(n)],
    "sorted": lambda n, rng: [float(i) for i in range(n)],
    "reversed": lambda n, rng: [float(n - i) for i in range(n)],
    "repeated": lambda n, rng: [float(rng.randint(0, 9)) for _ in range(n)],
    "adversarial": lambda n, rng: list(median_of_three_killer(n)),
}
CONFIG_LABELS = {
    "random": "Aleatorio (reales)",
    "random_int": "Aleatorio (enteros)",
    "sorted": "Ordenado",
    "reversed": "Inverso",
    "repeated": "Muy repetidos (10 valores)",
    "adversarial": "Adversario de mediana de 3",
}


def n_linear(n):
    return n


def n_log_n(n):
    return n * math.log2(n)


def n_squared(n):
    return n * n


# Expected growth per algorithm and configuration, from the formal analysis.
THEORY = {
    ("Bubble Sort", "random"): (n_squared, "n^2"),
    ("Bubble Sort", "random_int"): (n_squared, "n^2"),
    ("Bubble Sort", "sorted"): (n_linear, "n"),
    ("Bubble Sort", "reversed"): (n_squared, "n^2"),
    ("Bubble Sort", "repeated"): (n_squared, "n^2"),
    ("Bubble Sort", "adversarial"): (n_squared, "n^2"),
    ("Quicksort", "random"): (n_log_n, "n log n"),
    ("Quicksort", "random_int"): (n_log_n, "n log n"),
    ("Quicksort", "sorted"): (n_log_n, "n log n"),
    ("Quicksort", "reversed"): (n_log_n, "n log n"),
    ("Quicksort", "repeated"): (n_log_n, "n log n"),
    ("Quicksort", "adversarial"): (n_squared, "n^2"),
}


def measure(algorithm, data):
    """Time one run on a private copy. Copying and garbage collection stay out of the timer."""
    work = data.copy()
    gc.collect()
    gc.disable()
    try:
        start = time.perf_counter()
        algorithm(work)
        return time.perf_counter() - start
    finally:
        gc.enable()


def run_experiment(sizes, repetitions, configs, seed=42, on_progress=None, should_stop=None):
    """Return one row per timed run. Both algorithms get the same array in each repetition."""
    rows = []
    total = len(configs) * len(sizes) * repetitions * len(ALGORITHMS)
    done = 0
    names = list(ALGORITHMS)
    for config in configs:
        rng = random.Random(f"{seed}-{config}")
        for n in sizes:
            for repetition in range(repetitions):
                data = GENERATORS[config](n, rng)
                # Alternate who runs first so neither always gets a warm cache.
                order = names if repetition % 2 == 0 else names[::-1]
                for name in order:
                    if should_stop and should_stop():
                        return rows
                    seconds = measure(ALGORITHMS[name], data)
                    rows.append(
                        {"algorithm": name, "config": config, "n": n,
                         "repetition": repetition, "seconds": seconds}
                    )
                    done += 1
                    if on_progress:
                        on_progress(done, total, name, config, n)
    return rows


def summarize(rows):
    """Aggregate timed runs into median, mean, deviation and range per combination."""
    groups = {}
    for row in rows:
        groups.setdefault((row["algorithm"], row["config"], row["n"]), []).append(row["seconds"])
    summary = []
    for (algorithm, config, n), samples in groups.items():
        summary.append({
            "algorithm": algorithm, "config": config, "n": n, "runs": len(samples),
            "median_s": median(samples), "mean_s": fmean(samples),
            "stdev_s": stdev(samples) if len(samples) > 1 else 0.0,
            "min_s": min(samples), "max_s": max(samples),
        })
    return summary


def fit_slope(sizes, values):
    """Least-squares slope and R^2 of log(value) on log(n): T(n) = c*n^k gives slope k."""
    x, y = np.log(sizes), np.log(values)
    slope, intercept = np.polyfit(x, y, 1)
    residual = y - (slope * x + intercept)
    total = y - y.mean()
    denominator = float((total**2).sum())
    r_squared = 1 - float((residual**2).sum()) / denominator if denominator else 1.0
    return float(slope), r_squared


def growth_fits(summary):
    """Compare the measured growth with the theoretical curve for each combination."""
    series = {}
    for row in summary:
        series.setdefault((row["algorithm"], row["config"]), []).append((row["n"], row["median_s"]))
    fits = []
    for (algorithm, config), points in series.items():
        points.sort()
        sizes = [p[0] for p in points]
        times = [p[1] for p in points]
        growth, label = THEORY[algorithm, config]
        if len(sizes) < 2:
            continue
        slope, r_squared = fit_slope(sizes, times)
        theory_slope, _ = fit_slope(sizes, [growth(n) for n in sizes])
        fits.append({
            "algorithm": algorithm, "config": config, "theory": label,
            "measured_slope": slope, "theory_slope": theory_slope, "r_squared": r_squared,
            "largest_n": sizes[-1], "largest_median_s": times[-1],
            "doubling_ratio": times[-1] / times[-2] if sizes[-1] == 2 * sizes[-2] else None,
        })
    return fits


class CountingNumber:
    """Number that counts the comparisons made on it, for the untimed operation counts."""

    comparisons = 0
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        CountingNumber.comparisons += 1
        return self.value < other.value

    def __gt__(self, other):
        CountingNumber.comparisons += 1
        return self.value > other.value


class CountingList(list):
    """List that counts writes. Each swap performs exactly two."""

    writes = 0

    def __setitem__(self, index, value):
        CountingList.writes += 1
        super().__setitem__(index, value)


def count_operations(algorithm, data):
    """Run the real algorithm on counting values. Returns comparisons, swaps, max recursion depth."""
    CountingNumber.comparisons = 0
    CountingList.writes = 0
    work = CountingList(CountingNumber(v) for v in data)
    depth = {"current": 0, "max": 0}

    def profile(frame, event, _arg):
        if frame.f_code is _quicksort.__code__:
            if event == "call":
                depth["current"] += 1
                depth["max"] = max(depth["max"], depth["current"])
            elif event == "return":
                depth["current"] -= 1

    sys.setprofile(profile)
    try:
        algorithm(work)
    finally:
        sys.setprofile(None)
    return CountingNumber.comparisons, CountingList.writes // 2, depth["max"]


def run_operation_counts(sizes, repetitions, configs, seed=42, should_stop=None):
    """Count operations with the instrumented values. These runs are not timed."""
    rows = []
    for config in configs:
        rng = random.Random(f"{seed}-{config}-counts")
        for n in sizes:
            for repetition in range(repetitions):
                data = GENERATORS[config](n, rng)
                for name, algorithm in ALGORITHMS.items():
                    if should_stop and should_stop():
                        return rows
                    comparisons, swaps, depth = count_operations(algorithm, data)
                    rows.append({
                        "algorithm": name, "config": config, "n": n, "repetition": repetition,
                        "comparisons": comparisons, "swaps": swaps, "max_recursion_depth": depth,
                    })
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
