"""Tab that configures experiments, runs them off the GUI thread and shows charts and tables."""

import queue
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import theme
from section1_comparison.activity3_experiment.experiment import (
    CONFIG_LABELS,
    COUNT_REPETITIONS,
    DEFAULT_REPETITIONS,
    DEFAULT_SIZES,
    growth_fits,
    run_experiment,
    run_operation_counts,
    summarize,
)
from section1_comparison.activity4_results.charts import CHARTS, apply_chart_style
from section1_comparison.activity4_results.results_io import DELIVERABLES, load_saved, save_charts, save_data

MAX_SIZE = 50_000
# Counting operations costs about 50 times a normal run, so it stays on the smaller sizes.
MAX_COUNT_SIZE = 4000

# How to read each chart, by file name.
CHART_NOTES = {
    "01_time_vs_n_loglog": "Línea punteada: teoría c g(n), con g(n) = n, n log n o n² y c ajustada a las mediciones. "
                           "Banda: mínimo a máximo.",
    "02_time_vs_n_linear": "Mediana de las repeticiones. Muestra la configuración aleatoria (reales).",
    "03_speed_ratio": "Encima de la línea punteada, Bubble Sort tarda más. Debajo, tarda menos.",
    "04_time_over_theory": "Una serie plana significa que el crecimiento medido coincide con la teoría.",
    "05_comparisons": "Cota de Bubble Sort: n(n-1)/2, o n-1 si ya está ordenado. Puede quedar por debajo porque se "
                      "detiene si una pasada no intercambia nada.",
    "06_swaps": "Un punto en cero significa que no hubo ningún intercambio.",
    "07_recursion_depth": "Adversario: arreglo construido con el método de McIlroy (1999) para que la mediana de 3 "
                          "elija malos pivotes.",
}

# Short forms for the tables, whose columns must all fit beside the side panel.
TABLE_ALGORITHMS = {"Bubble Sort": "Bubble", "Quicksort": "Quicksort"}
TABLE_CONFIGS = {"random": "Reales", "random_int": "Enteros", "sorted": "Ordenado", "reversed": "Inverso",
                 "repeated": "Repetidos", "adversarial": "Adversario"}

TABLES = {
    "Resumen": ("summary", {"algorithm": "Algoritmo", "config": "Datos", "n": "n", "runs": "Corridas",
                            "median_s": "Mediana (s)", "mean_s": "Media (s)", "stdev_s": "Desv. est. (s)",
                            "min_s": "Mínimo (s)", "max_s": "Máximo (s)"}),
    "Ajuste": ("fits", {"algorithm": "Algoritmo", "config": "Datos",
                        "measured_slope": "k med.", "theory_slope": "k teór.",
                        "r_squared": "R²", "doubling_ratio": "T(2n)/T(n)", "theory": "Teoría"}),
    "Operaciones": ("operations", {"algorithm": "Algoritmo", "config": "Datos", "n": "n",
                                   "repetition": "Repetición", "comparisons": "Comparaciones",
                                   "swaps": "Intercambios", "max_recursion_depth": "Prof. recursión"}),
    "Crudos": ("raw", {"algorithm": "Algoritmo", "config": "Datos", "n": "n",
                             "repetition": "Repetición", "seconds": "Tiempo (s)"}),
}


def parse_sizes(text):
    """Read the sizes typed by the user. Raises ValueError with a message for the screen."""
    try:
        sizes = {int(part) for part in text.replace(";", ",").replace(" ", ",").split(",") if part}
    except ValueError:
        raise ValueError("Los tamaños deben ser enteros separados por comas.") from None
    if len(sizes) < 2:
        raise ValueError("Escriba al menos dos tamaños distintos para ver el crecimiento.")
    if min(sizes) < 2 or max(sizes) > MAX_SIZE:
        raise ValueError(f"Cada tamaño debe estar entre 2 y {MAX_SIZE}.")
    return sorted(sizes)


def format_cell(key, value):
    if value is None:
        return "no aplica"
    if key == "config":
        return TABLE_CONFIGS[value]
    if key == "algorithm":
        return TABLE_ALGORITHMS[value]
    if isinstance(value, float):
        return f"{value:.3f}" if key in ("measured_slope", "theory_slope", "r_squared", "doubling_ratio") else f"{value:.6g}"
    return str(value)


class ComparisonTab(ttk.Frame):
    def __init__(self, master, fonts):
        super().__init__(master, style="TFrame")
        self.fonts = fonts
        self.results = load_saved(DELIVERABLES / "data") or {"raw": [], "summary": [], "fits": [], "operations": []}
        self.events = queue.Queue()
        self.stop_flag = threading.Event()
        self.worker = None
        apply_chart_style()
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_controls()
        self._build_results()
        if self.results["raw"]:
            self.status.set("Se muestran los resultados guardados del experimento completo.")
        else:
            self.status.set("Aún no hay resultados. Configure el experimento y pulse Ejecutar.")
        self._refresh()

    def _build_controls(self):
        panel = ttk.Frame(self, style="Panel.TFrame", padding=theme.SPACE_L)
        panel.grid(row=0, column=0, sticky="ns")
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="Experimento", style="Heading.TLabel").grid(sticky="w", pady=(0, theme.SPACE_M))
        ttk.Label(panel, text="Tamaños n, separados por comas", style="Panel.TLabel").grid(sticky="w")
        self.sizes = tk.StringVar(value=",".join(str(n) for n in DEFAULT_SIZES))
        ttk.Entry(panel, textvariable=self.sizes, width=20).grid(sticky="ew", pady=(theme.SPACE_XS, 0))
        self.sizes_error = ttk.Label(panel, style="Error.TLabel", wraplength=theme.PANEL_TEXT_WIDTH, justify="left")
        self.sizes_error.grid(sticky="w")
        self.sizes_error.grid_remove()

        ttk.Label(panel, text="Repeticiones por combinación", style="Panel.TLabel").grid(sticky="w", pady=(theme.SPACE_S, 0))
        self.repetitions = tk.IntVar(value=DEFAULT_REPETITIONS)
        ttk.Spinbox(panel, from_=1, to=50, textvariable=self.repetitions, width=6, state="readonly").grid(
            sticky="w", pady=(theme.SPACE_XS, theme.SPACE_M))

        ttk.Label(panel, text="Configuraciones iniciales", style="Panel.TLabel").grid(sticky="w")
        self.config_vars = {}
        for key, label in CONFIG_LABELS.items():
            variable = tk.BooleanVar(value=True)
            self.config_vars[key] = variable
            ttk.Checkbutton(panel, text=label, variable=variable).grid(sticky="w", pady=1)

        self.count_operations = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text=f"Contar operaciones (hasta n = {MAX_COUNT_SIZE})",
                        variable=self.count_operations).grid(sticky="w", pady=(theme.SPACE_M, 0))

        buttons = ttk.Frame(panel, style="Panel.TFrame")
        buttons.grid(sticky="ew", pady=(theme.SPACE_L, theme.SPACE_S))
        self.run_button = ttk.Button(buttons, text="Ejecutar", style="Primary.TButton", command=self._start)
        self.run_button.pack(side="left")
        self.stop_button = ttk.Button(buttons, text="Detener", command=self._stop, state="disabled")
        self.stop_button.pack(side="left", padx=(theme.SPACE_XS, 0))
        self.save_button = ttk.Button(buttons, text="Guardar...", command=self._save)
        self.save_button.pack(side="left", padx=(theme.SPACE_XS, 0))

        self.progress = ttk.Progressbar(panel, maximum=1.0)
        self.progress.grid(sticky="ew")
        self.status = tk.StringVar()
        ttk.Label(panel, textvariable=self.status, style="Hint.TLabel", wraplength=theme.PANEL_TEXT_WIDTH,
                  justify="left").grid(sticky="w", pady=(theme.SPACE_S, 0))

    def _build_results(self):
        self.notebook = ttk.Notebook(self, style="Inner.TNotebook")
        self.notebook.grid(row=0, column=1, sticky="nsew", padx=(theme.SPACE_M, theme.SPACE_M), pady=(0, theme.SPACE_M))

        charts_page = ttk.Frame(self.notebook, style="Panel.TFrame", padding=theme.SPACE_S)
        self.notebook.add(charts_page, text="Gráficas")
        charts_page.columnconfigure(0, weight=1)
        charts_page.rowconfigure(2, weight=1)
        self.chart_choice = tk.StringVar(value=CHARTS[0][0])
        picker = ttk.Combobox(charts_page, textvariable=self.chart_choice, state="readonly",
                              values=[chart[0] for chart in CHARTS], width=50)
        picker.grid(row=0, column=0, sticky="w", pady=(0, theme.SPACE_S))
        picker.bind("<<ComboboxSelected>>", lambda _: self._draw_chart())
        self.chart_note = ttk.Label(charts_page, style="Hint.TLabel", justify="left")
        self.chart_note.grid(row=1, column=0, sticky="w", pady=(0, theme.SPACE_S))
        charts_page.bind("<Configure>", lambda event: self.chart_note.configure(wraplength=event.width - 2 * theme.SPACE_S))

        self.figure = Figure(dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=charts_page)
        self.canvas.get_tk_widget().grid(row=2, column=0, sticky="nsew")
        toolbar_frame = ttk.Frame(charts_page, style="Panel.TFrame")
        toolbar_frame.grid(row=3, column=0, sticky="ew")
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame, pack_toolbar=False)
        toolbar.configure(background=theme.SURFACE)
        toolbar._message_label.configure(background=theme.SURFACE, foreground=theme.TEXT_SECONDARY)
        for child in toolbar.winfo_children():
            child.configure(background=theme.SURFACE)
        toolbar.pack(side="left", fill="x")
        # 424 s measured for the full experiment (section3_deliverables/data/environment.txt).
        method_note = ttk.Label(charts_page, text="El tiempo solo mide el algoritmo, sin generar datos ni dibujar. "
                                                  "El experimento completo tardó unos 7 minutos en el equipo de prueba.",
                                style="Hint.TLabel", justify="left")
        method_note.grid(row=4, column=0, sticky="w")
        charts_page.bind("<Configure>", lambda event: method_note.configure(wraplength=event.width - 2 * theme.SPACE_S), add="+")

        self.tables = {}
        self.cell_font = tkfont.Font(font=self.fonts.code)
        self.heading_font = tkfont.Font(font=self.fonts.small)
        for title, (key, columns) in TABLES.items():
            page = ttk.Frame(self.notebook, style="Panel.TFrame", padding=theme.SPACE_S)
            self.notebook.add(page, text=title)
            page.columnconfigure(0, weight=1)
            page.rowconfigure(1, weight=1)
            empty = ttk.Label(page, style="Hint.TLabel")
            empty.grid(row=0, column=0, sticky="w")
            if key == "fits":
                # Row 0 is free here unless the table is empty; say what k means for a reader of the table.
                self.fits_note = "k: pendiente log-log, T(n) = c n^k. Reales y Enteros son aleatorios."
            tree = ttk.Treeview(page, columns=list(columns), show="headings")
            for column, heading in columns.items():
                text_column = column in ("config", "algorithm")
                tree.heading(column, text=heading)
                tree.column(column, anchor="w" if text_column else "e", stretch=False)
            scroll = ttk.Scrollbar(page, orient="vertical", command=tree.yview)
            scroll_x = ttk.Scrollbar(page, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=scroll.set, xscrollcommand=scroll_x.set)
            tree.grid(row=1, column=0, sticky="nsew")
            scroll.grid(row=1, column=1, sticky="ns")
            scroll_x.grid(row=2, column=0, sticky="ew")
            self.tables[key] = (tree, columns, empty)

    def _refresh(self):
        self._draw_chart()
        for key, (tree, columns, empty) in self.tables.items():
            tree.delete(*tree.get_children())
            rows = self.results[key]
            if not rows:
                if key == "operations":
                    empty.configure(text="Sin conteos. Active 'Contar operaciones' y ejecute el experimento.")
                else:
                    empty.configure(text="Sin resultados todavía. Pulse Ejecutar.")
                continue
            empty.configure(text=self.fits_note if key == "fits" else "")
            cells = {column: [format_cell(column, row.get(column)) for row in rows] for column in columns}
            for values in zip(*cells.values()):
                tree.insert("", "end", values=values)
            # Size each column to its real text, so nothing is clipped at any font scale.
            for column, heading in columns.items():
                width = max(self.heading_font.measure(heading), self.cell_font.measure(max(cells[column], key=len)))
                tree.column(column, width=width + theme.SPACE_M)
        self.save_button.configure(state="normal" if self.results["raw"] else "disabled")

    def _draw_chart(self):
        title = self.chart_choice.get()
        _, draw, needs, stem = next(chart for chart in CHARTS if chart[0] == title)
        self.chart_note.configure(text=CHART_NOTES[stem])
        self.figure.clear()
        if self.results[needs]:
            draw(self.figure, self.results)
        else:
            reason = ("Esta gráfica necesita los conteos. Active 'Contar operaciones' y ejecute el experimento."
                      if needs == "operations" else "Aún no hay tiempos medidos. Pulse Ejecutar.")
            self.figure.text(0.5, 0.5, reason, ha="center", va="center", color=theme.TEXT_SECONDARY, fontsize=12)
        self.canvas.draw_idle()

    def _start(self):
        self.sizes_error.grid_remove()
        try:
            sizes = parse_sizes(self.sizes.get())
        except ValueError as error:
            self.sizes_error.configure(text=str(error))
            self.sizes_error.grid()
            return
        configs = [key for key, variable in self.config_vars.items() if variable.get()]
        if not configs:
            self.status.set("Seleccione al menos una configuración inicial.")
            return
        repetitions = self.repetitions.get()
        count = self.count_operations.get()
        count_sizes = [n for n in sizes if n <= MAX_COUNT_SIZE]

        self.stop_flag.clear()
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress.configure(value=0)
        self.status.set("Midiendo...")

        def work():
            try:
                rows = run_experiment(
                    sizes, repetitions, configs,
                    on_progress=lambda *args: self.events.put(("progress", args)),
                    should_stop=self.stop_flag.is_set,
                )
                # None means "not recounted", which keeps the counts already on screen.
                operations = None
                if count and count_sizes and not self.stop_flag.is_set():
                    self.events.put(("counting", None))
                    counted = run_operation_counts(count_sizes, COUNT_REPETITIONS, configs,
                                                   should_stop=self.stop_flag.is_set)
                    if not self.stop_flag.is_set():
                        operations = counted
                self.events.put(("done", (rows, operations)))
            except Exception as error:
                self.events.put(("error", error))

        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()
        self.after(theme.POLL_MS, self._poll)

    def _stop(self):
        self.stop_flag.set()
        self.stop_button.configure(state="disabled")
        self.status.set("Deteniendo al terminar la corrida actual...")

    def _poll(self):
        finished = False
        while not self.events.empty():
            kind, payload = self.events.get()
            if kind == "progress" and not self.stop_flag.is_set():
                done, total, name, config, n = payload
                self.progress.configure(value=done / total)
                self.status.set(f"Corrida {done} de {total}: {name}, {CONFIG_LABELS[config].lower()}, n = {n}.")
            elif kind == "counting":
                self.status.set("Contando operaciones. Esto no se cronometra.")
            elif kind == "done":
                self._finish(*payload)
                finished = True
            elif kind == "error":
                self.status.set(f"El experimento falló: {payload}. Los resultados anteriores no cambiaron.")
                finished = True
        if finished:
            self.run_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
        else:
            self.after(theme.POLL_MS, self._poll)

    def _finish(self, rows, operations):
        if not rows:
            self.status.set("Detenido antes de completar una corrida. Los resultados anteriores no cambiaron.")
            return
        summary = summarize(rows)
        kept_counts = operations is None and bool(self.results["operations"])
        if operations is None:
            operations = self.results["operations"]
        self.results = {"raw": rows, "summary": summary, "fits": growth_fits(summary), "operations": operations}
        stopped = self.stop_flag.is_set()
        self.status.set(
            (f"Detenido con {len(rows)} corridas completas. Se muestran solo esas." if stopped
             else f"Experimento terminado con {len(rows)} corridas. Estos resultados aún no están guardados.")
            + (" Los conteos de operaciones son de la corrida anterior." if kept_counts else "")
        )
        self._refresh()

    def _save(self):
        folder = filedialog.askdirectory(title="Carpeta para guardar datos y gráficas", mustexist=False)
        if not folder:
            return
        try:
            save_data(f"{folder}/data", self.results)
            saved = save_charts(f"{folder}/charts", self.results)
        except OSError as error:
            self.status.set(f"No se pudo guardar: {error}. Elija otra carpeta.")
            return
        finally:
            apply_chart_style()
        self.status.set(f"Guardado en {folder}: datos y {len(saved)} gráficas.")
