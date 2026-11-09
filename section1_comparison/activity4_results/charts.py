"""Comparison charts. Each function draws on a Matplotlib Figure, for the GUI and for the saved files."""

import math
from statistics import median

import matplotlib
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter

import theme
from section1_comparison.activity3_experiment.experiment import ALGORITHMS, CONFIG_LABELS, THEORY

COLORS = {"Bubble Sort": theme.BUBBLE, "Quicksort": theme.QUICK}
MARKERS = {"Bubble Sort": "o", "Quicksort": "s"}
TEX = {"n": "$n$", "n log n": r"$n \log n$", "n^2": "$n^2$"}
# Three panels share the width, so the panel titles must stay short.
PANEL_TITLES = {**CONFIG_LABELS, "repeated": "Muy repetidos", "adversarial": "Adversario mediana 3"}


def apply_chart_style():
    matplotlib.rcParams.update({
        "font.family": "sans-serif",
        # DejaVu ships inside Matplotlib with a real bold; the UI's first choices may have none.
        "font.sans-serif": ["DejaVu Sans"],
        "mathtext.fontset": "dejavusans",
        "font.size": 10,
        "legend.fontsize": 9,
        "axes.edgecolor": theme.BORDER_STRONG,
        "axes.labelcolor": theme.TEXT_SECONDARY,
        "axes.titlecolor": theme.INK,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.grid": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.facecolor": theme.CHART_SURFACE,
        "figure.facecolor": theme.CHART_SURFACE,
        "grid.color": theme.CHART_GRID,
        "grid.linewidth": 0.8,
        "xtick.color": theme.TEXT_SECONDARY,
        "ytick.color": theme.TEXT_SECONDARY,
        "lines.linewidth": 2,
        "lines.markersize": 5,
        "savefig.facecolor": theme.CHART_SURFACE,
    })


def _series(rows, algorithm, config, field):
    """Return sorted (n, value) points. Repeated rows for one n are reduced to their median."""
    groups = {}
    for row in rows:
        if row["algorithm"] == algorithm and row["config"] == config:
            groups.setdefault(row["n"], []).append(row[field])
    return [(n, median(groups[n])) for n in sorted(groups)]


def _configs_in(rows):
    seen = [row["config"] for row in rows]
    return [config for config in CONFIG_LABELS if config in seen]


def _panels(figure, configs, sharey=True):
    columns = min(3, len(configs))
    rows = math.ceil(len(configs) / columns)
    axes = figure.subplots(rows, columns, sharex=True, sharey=sharey, squeeze=False).ravel()
    for ax in axes[len(configs):]:
        ax.set_visible(False)
    return axes[:len(configs)], columns, rows


def _label_axes(axes, columns, x_label, y_label, rows):
    last_row_start = len(axes) - columns
    sizes = sorted({row["n"] for row in rows})
    ticks = sizes[::2] if len(sizes) > 4 else sizes
    # One label for the whole figure: one per row collide when the window is short.
    axes[0].figure.supylabel(y_label, fontsize=10, color=theme.TEXT_SECONDARY)
    for index, ax in enumerate(axes):
        # Tick at the measured sizes: the default log ticks overlap when the range is short.
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g}k" if value >= 1000 else f"{value:g}"))
        ax.xaxis.set_minor_formatter(NullFormatter())
        if index >= last_row_start:
            ax.set_xlabel(x_label)


def _legend(figure, handles):
    # Constrained layout recomputes on every draw, so the legend clears the axis labels at any window size.
    figure.set_layout_engine("constrained")
    figure.legend(handles=handles, loc="outside lower center", ncol=len(handles), frameon=False)


def _measured_handle(name):
    return Line2D([], [], color=COLORS[name], marker=MARKERS[name], label=f"{name}, medido")


def _fit_constant(points, growth):
    """Least-squares constant c in T(n) = c*g(n) on the log scale, so only the shape is compared."""
    logs = [math.log(value) - math.log(growth(n)) for n, value in points if value > 0]
    return math.exp(sum(logs) / len(logs)) if logs else None


def time_loglog(figure, data):
    summary = data["summary"]
    configs = _configs_in(summary)
    axes, columns, _ = _panels(figure, configs)
    for ax, config in zip(axes, configs):
        series = {name: _series(summary, name, config, "median_s") for name in ALGORITHMS}
        slowest = max((name for name in ALGORITHMS if series[name]), key=lambda name: series[name][-1][1])
        for name, points in series.items():
            if not points:
                continue
            xs = [p[0] for p in points]
            low = [p[1] for p in _series(summary, name, config, "min_s")]
            high = [p[1] for p in _series(summary, name, config, "max_s")]
            ys = [p[1] for p in points]
            ax.fill_between(xs, low, high, color=COLORS[name], alpha=0.18, linewidth=0)
            ax.loglog(xs, ys, color=COLORS[name], marker=MARKERS[name])
            growth, label = THEORY[name, config]
            c = _fit_constant(points, growth)
            ax.loglog(xs, [c * growth(n) for n in xs], "--", color=COLORS[name], linewidth=1)
            # On the free side of the line: the slower series above, the faster one below.
            ax.annotate(TEX[label], (xs[-1], ys[-1]), xytext=(0, 8 if name == slowest else -20),
                        textcoords="offset points", ha="right", color=theme.INK, fontsize=9)
        # Headroom, so the label of the top series stays clear of the panel title.
        ax.margins(y=0.15)
        ax.set_title(PANEL_TITLES[config])
    _label_axes(axes, columns, "Tamaño n (escala log)", "Tiempo en s (escala log)", summary)
    _legend(figure, [
        _measured_handle("Bubble Sort"), _measured_handle("Quicksort"),
        Line2D([], [], color=theme.TEXT_MUTED, linestyle="--", linewidth=1, label="Teoría con c ajustada"),
    ])


def time_linear(figure, data):
    summary = data["summary"]
    configs = _configs_in(summary)
    config = "random" if "random" in configs else configs[0]
    ax = figure.subplots()
    for name in ALGORITHMS:
        points = _series(summary, name, config, "median_s")
        if not points:
            continue
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        ax.plot(xs, ys, color=COLORS[name], marker=MARKERS[name], clip_on=False)
        ax.annotate(f"{name}: {ys[-1]:.3g} s", (xs[-1], ys[-1]), xytext=(-6, 8), textcoords="offset points",
                    ha="right", color=theme.INK)
    ax.set_title(CONFIG_LABELS[config])
    ax.set_xlabel("Tamaño n")
    ax.set_ylabel("Tiempo en s")
    ax.set_ylim(bottom=0)
    _legend(figure, [_measured_handle(name) for name in ALGORITHMS])


def speed_ratio(figure, data):
    summary = data["summary"]
    configs = _configs_in(summary)
    axes, columns, _ = _panels(figure, configs)
    for ax, config in zip(axes, configs):
        bubble = dict(_series(summary, "Bubble Sort", config, "median_s"))
        quick = dict(_series(summary, "Quicksort", config, "median_s"))
        common = [n for n in bubble if n in quick]
        if not common:
            continue
        ratios = [bubble[n] / quick[n] for n in common]
        ax.loglog(common, ratios, color=theme.INK, marker="D")
        ax.axhline(1, color=theme.TEXT_MUTED, linestyle="--", linewidth=1)
        last = ratios[-1]
        text = f"{1 / last:.2g} veces más rápido" if last < 1 else f"{last:.0f} veces" if last >= 10 else f"{last:.2g} veces"
        ax.annotate(text, (common[-1], last), xytext=(0, 8), textcoords="offset points", ha="right", color=theme.INK)
        ax.set_title(PANEL_TITLES[config])
    _label_axes(axes, columns, "Tamaño n (escala log)", "Tiempo Bubble / Quicksort", summary)
    _legend(figure, [
        Line2D([], [], color=theme.INK, marker="D", label="Razón medida"),
        Line2D([], [], color=theme.TEXT_MUTED, linestyle="--", linewidth=1, label="Mismo tiempo (razón = 1)"),
    ])


def normalized_theory(figure, data):
    summary = data["summary"]
    configs = _configs_in(summary)
    axes, columns, _ = _panels(figure, configs)
    for ax, config in zip(axes, configs):
        for name in ALGORITHMS:
            points = _series(summary, name, config, "median_s")
            if not points:
                continue
            growth, _ = THEORY[name, config]
            xs = [p[0] for p in points]
            c = _fit_constant(points, growth)
            ax.semilogx(xs, [value / (c * growth(n)) for n, value in points],
                        color=COLORS[name], marker=MARKERS[name])
        ax.axhline(1, color=theme.TEXT_MUTED, linestyle="--", linewidth=1)
        ax.set_title(PANEL_TITLES[config])
    _label_axes(axes, columns, "Tamaño n (escala log)", "T(n) / (c g(n))", summary)
    _legend(figure, [
        _measured_handle("Bubble Sort"), _measured_handle("Quicksort"),
        Line2D([], [], color=theme.TEXT_MUTED, linestyle="--", linewidth=1, label="Coincide con la teoría (= 1)"),
    ])


def comparisons_chart(figure, data):
    operations = data["operations"]
    configs = _configs_in(operations)
    axes, columns, _ = _panels(figure, configs)
    for ax, config in zip(axes, configs):
        for name in ALGORITHMS:
            points = _series(operations, name, config, "comparisons")
            if not points:
                continue
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            ax.loglog(xs, ys, color=COLORS[name], marker=MARKERS[name])
            growth, _ = THEORY[name, config]
            if name == "Bubble Sort":
                exact = [n - 1 if config == "sorted" else n * (n - 1) / 2 for n in xs]
            else:
                c = _fit_constant(points, growth)
                exact = [c * growth(n) for n in xs]
            ax.loglog(xs, exact, "--", color=COLORS[name], linewidth=1)
        ax.set_title(PANEL_TITLES[config])
    _label_axes(axes, columns, "Tamaño n (escala log)", "Comparaciones (escala log)", operations)
    _legend(figure, [
        _measured_handle("Bubble Sort"), _measured_handle("Quicksort"),
        Line2D([], [], color=theme.TEXT_MUTED, linestyle="--", linewidth=1,
               label="Cota de Bubble; Quicksort con c ajustada"),
    ])


def swaps_chart(figure, data):
    operations = data["operations"]
    configs = _configs_in(operations)
    axes, columns, _ = _panels(figure, configs)
    for ax, config in zip(axes, configs):
        for name in ALGORITHMS:
            points = _series(operations, name, config, "swaps")
            if not points:
                continue
            ax.plot([p[0] for p in points], [p[1] for p in points], color=COLORS[name], marker=MARKERS[name])
        ax.set_xscale("log")
        ax.set_yscale("symlog", linthresh=1)
        ax.set_title(PANEL_TITLES[config])
    _label_axes(axes, columns, "Tamaño n (escala log)", "Intercambios (log, con cero)", operations)
    _legend(figure, [_measured_handle(name) for name in ALGORITHMS])


def recursion_depth(figure, data):
    operations = data["operations"]
    configs = _configs_in(operations)
    axes, columns, _ = _panels(figure, configs)
    for ax, config in zip(axes, configs):
        points = _series(operations, "Quicksort", config, "max_recursion_depth")
        if not points:
            continue
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        ax.loglog(xs, ys, color=theme.QUICK, marker=MARKERS["Quicksort"])
        ax.loglog(xs, [math.log2(n) for n in xs], "--", color=theme.TEXT_MUTED, linewidth=1)
        ax.loglog(xs, [n / 2 for n in xs], ":", color=theme.TEXT_MUTED, linewidth=1.2)
        ax.set_title(PANEL_TITLES[config])
    _label_axes(axes, columns, "Tamaño n (escala log)", "Profundidad máxima de recursión", operations)
    _legend(figure, [
        Line2D([], [], color=theme.QUICK, marker=MARKERS["Quicksort"], label="Quicksort, medido"),
        Line2D([], [], color=theme.TEXT_MUTED, linestyle="--", linewidth=1, label="$\\log_2 n$"),
        Line2D([], [], color=theme.TEXT_MUTED, linestyle=":", linewidth=1.2, label="$n/2$"),
    ])


# Title, drawing function, the data it needs, file name.
CHARTS = [
    ("Tiempo contra tamaño (log-log) y curva teórica", time_loglog, "summary", "01_time_vs_n_loglog"),
    ("Tiempo en escala lineal", time_linear, "summary", "02_time_vs_n_linear"),
    ("Cuántas veces es más lento Bubble Sort", speed_ratio, "summary", "03_speed_ratio"),
    ("Tiempo dividido por la curva teórica", normalized_theory, "summary", "04_time_over_theory"),
    ("Comparaciones contadas", comparisons_chart, "operations", "05_comparisons"),
    ("Intercambios contados", swaps_chart, "operations", "06_swaps"),
    ("Profundidad de recursión de Quicksort", recursion_depth, "operations", "07_recursion_depth"),
]
