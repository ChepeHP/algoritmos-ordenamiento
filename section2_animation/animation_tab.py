"""Tab that animates Quicksort on a Tkinter Canvas by replaying the real algorithm's events."""

import random
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

import theme
from section2_animation.replay import (
    CODE_LINES,
    KINDS,
    MAX_ELEMENTS,
    MIN_ELEMENTS,
    ORDERS,
    QuicksortReplay,
    decimal_comma_note,
    format_value,
    generate_values,
    parse_values,
)

LEFT_MARGIN = 44
RIGHT_MARGIN = 18
# The rows above the bars, from the top: pivot label, partition labels, partition brackets, bar values.
REGION_TOP = 4
PIVOT_ROW = 14
SPLIT_LABEL_ROW = 30
SPLIT_LINE_ROW = 38
TOP_MARGIN = 58
BAR_GAP = 3
INDEX_ROW = 16
NEGATIVE_LABEL_ROOM = 18
POINTER_ROW = 34
TREE_SHARE = 0.30
TREE_ROW_MAX = 16
# Room a value takes above its bar when it is written horizontally.
FLAT_LABEL_ROOM = 16
ROTATED_LABEL_GAP = 3
TYPED_ORDER = "Escrito por usted"
TEXT_INPUTS = (ttk.Entry, ttk.Spinbox, ttk.Combobox)

LEGEND = [
    (theme.PLOT_BAR, "Pendiente"),
    (theme.STATE_COMPARE, "Comparación (i, j)"),
    (theme.STATE_SWAP, "Intercambio (se mueve)"),
    (theme.STATE_PIVOT, "Pivote (p)"),
    (theme.STATE_SORTED, "Posición final (línea)"),
    (theme.PLOT_BAR_DIM, "Fuera de la llamada"),
]


class AnimationTab(ttk.Frame):
    def __init__(self, master, fonts):
        super().__init__(master)
        self.fonts = fonts
        self.small_font = tkfont.Font(font=fonts.plot_small)
        self.state = "idle"
        self.timer = None
        self.swap_start = None
        self.swap_duration = 0
        self.rng = random.Random()
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_controls()
        self._build_stage()
        self._bind_keys()
        self.generate()

    def _build_controls(self):
        panel = ttk.Frame(self, style="Panel.TFrame", padding=theme.SPACE_L)
        panel.grid(row=0, column=0, sticky="ns")

        ttk.Label(panel, text="Datos de entrada", style="Heading.TLabel").grid(sticky="w", pady=(0, theme.SPACE_S))
        ttk.Label(panel, text=f"Escriba entre {MIN_ELEMENTS} y {MAX_ELEMENTS} números", style="Panel.TLabel").grid(sticky="w")
        entry_row = ttk.Frame(panel, style="Panel.TFrame")
        entry_row.grid(sticky="ew", pady=(theme.SPACE_XS, 0))
        entry_row.columnconfigure(0, weight=1)
        self.input_text = tk.StringVar()
        entry = ttk.Entry(entry_row, textvariable=self.input_text, width=18)
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<Return>", lambda _: self.apply_input())
        ttk.Button(entry_row, text="Usar", command=self.apply_input, width=5).grid(row=0, column=1, padx=(theme.SPACE_XS, 0))
        self.input_error = ttk.Label(panel, style="Error.TLabel", wraplength=theme.PANEL_TEXT_WIDTH, justify="left")
        self.input_error.grid(sticky="w")
        self.input_error.grid_remove()

        form = ttk.Frame(panel, style="Panel.TFrame")
        form.grid(sticky="ew", pady=(theme.SPACE_S, 0))
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Orden", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, theme.SPACE_S))
        self.order = tk.StringVar(value=ORDERS["random"])
        ttk.Combobox(form, textvariable=self.order, values=list(ORDERS.values()), state="readonly", width=14).grid(
            row=0, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="Tipo", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=(0, theme.SPACE_S))
        self.kind = tk.StringVar(value=KINDS["int"])
        ttk.Combobox(form, textvariable=self.kind, values=list(KINDS.values()), state="readonly", width=14).grid(
            row=1, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="Tamaño", style="Panel.TLabel").grid(row=2, column=0, sticky="w", padx=(0, theme.SPACE_S))
        self.size = tk.IntVar(value=14)
        size_row = ttk.Frame(form, style="Panel.TFrame")
        size_row.grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Spinbox(size_row, from_=MIN_ELEMENTS, to=MAX_ELEMENTS, textvariable=self.size, width=4).pack(side="left")
        ttk.Button(size_row, text="Generar arreglo", command=self.generate).pack(side="right")

        ttk.Label(panel, text="Reproducción", style="Heading.TLabel").grid(sticky="w", pady=(theme.SPACE_M, theme.SPACE_S))
        transport = ttk.Frame(panel, style="Panel.TFrame")
        transport.grid(sticky="w")
        self.play_button = ttk.Button(transport, text="Iniciar", style="Primary.TButton", width=8, command=self.toggle)
        self.play_button.pack(side="left")
        self.back_button = ttk.Button(transport, text="Atrás", width=5, command=self.step_back)
        self.back_button.pack(side="left", padx=(theme.SPACE_XS, 0))
        self.step_button = ttk.Button(transport, text="Paso", width=4, command=self.single_step)
        self.step_button.pack(side="left", padx=(theme.SPACE_XS, 0))
        self.reset_button = ttk.Button(transport, text="Reiniciar", width=7, command=self.reset)
        self.reset_button.pack(side="left", padx=(theme.SPACE_XS, 0))
        ttk.Label(panel, text="Teclado: Espacio inicia o pausa, las flechas avanzan o retroceden un paso, R reinicia.",
                  style="Hint.TLabel", wraplength=theme.PANEL_TEXT_WIDTH, justify="left").grid(sticky="w", pady=(theme.SPACE_XS, 0))

        speed_row = ttk.Frame(panel, style="Panel.TFrame")
        speed_row.grid(sticky="ew", pady=(theme.SPACE_M, 0))
        speed_row.columnconfigure(1, weight=1)
        ttk.Label(speed_row, text="Velocidad", style="Panel.TLabel").grid(row=0, column=0, padx=(0, theme.SPACE_S))
        self.speed_exponent = tk.DoubleVar(value=0)
        ttk.Scale(speed_row, from_=-2, to=3, variable=self.speed_exponent, command=self._update_speed_label).grid(
            row=0, column=1, sticky="ew")
        self.speed_label = ttk.Label(speed_row, text="1x", style="Value.TLabel", width=6, anchor="e")
        self.speed_label.grid(row=0, column=2)
        self.reduce_motion = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text="Reducir movimiento", variable=self.reduce_motion).grid(sticky="w", pady=(theme.SPACE_XS, 0))

        ttk.Label(panel, text="Código en ejecución", style="Heading.TLabel").grid(sticky="w", pady=(theme.SPACE_L, theme.SPACE_XS))
        # Takes the height that is left and scrolls to the current line, so it fits any window.
        panel.rowconfigure(panel.grid_size()[1], weight=1)
        self.code = tk.Text(panel, height=3, width=45, font=self.fonts.plot_small, wrap="none",
                            bg=theme.SURFACE, fg=theme.TEXT_SECONDARY, relief="flat", highlightthickness=0,
                            cursor="arrow", spacing1=1, spacing3=1, takefocus=0)
        self.code.insert("1.0", "\n".join(CODE_LINES))
        self.code.tag_configure("current", background=theme.INK, foreground=theme.ON_INK)
        self.code.configure(state="disabled")
        self.code.grid(sticky="nsw")

    def _build_stage(self):
        stage = ttk.Frame(self, padding=(theme.SPACE_L, theme.SPACE_M, theme.SPACE_L, theme.SPACE_M))
        stage.grid(row=0, column=1, sticky="nsew")
        stage.columnconfigure(0, weight=1)
        stage.rowconfigure(1, weight=1)

        # Fixed at two lines, so a longer sentence does not resize the plot in mid-animation.
        narration_box = ttk.Frame(stage, height=2 * tkfont.Font(font=self.fonts.narration).metrics("linespace"))
        narration_box.grid(row=0, column=0, sticky="ew", pady=(0, theme.SPACE_S))
        narration_box.pack_propagate(False)
        self.narration = ttk.Label(narration_box, style="Narration.TLabel", anchor="w", justify="left")
        self.narration.pack(fill="both", expand=True)
        narration_box.bind("<Configure>", lambda event: self.narration.configure(wraplength=event.width))
        self.canvas = tk.Canvas(stage, bg=theme.INK, takefocus=1, highlightthickness=2,
                                highlightbackground=theme.PAGE, highlightcolor=theme.INK_HOVER)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _: self.draw())

        footer = ttk.Frame(stage)
        footer.grid(row=2, column=0, sticky="ew", pady=(theme.SPACE_S, 0))
        footer.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(footer, maximum=1.0)
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, theme.SPACE_M))
        self.step_label = ttk.Label(footer, style="Step.TLabel", width=17, anchor="e")
        self.step_label.grid(row=0, column=1)

        counters = ttk.Frame(stage)
        counters.grid(row=3, column=0, sticky="w", pady=(theme.SPACE_XS, 0))
        self.comparisons_label = self._counter(counters, "Comparaciones")
        self.swaps_label = self._counter(counters, "Intercambios")
        self.depth_label = self._counter(counters, "Profundidad")

        legend = ttk.Frame(stage)
        legend.grid(row=4, column=0, sticky="w", pady=(theme.SPACE_XS, 0))
        for index, (color, text) in enumerate(LEGEND):
            row, column = divmod(index, 3)
            cell = ttk.Frame(legend)
            cell.grid(row=row, column=column, sticky="w", padx=(0, theme.SPACE_M))
            tk.Canvas(cell, width=12, height=12, bg=color, highlightthickness=0).pack(side="left", padx=(0, theme.SPACE_XS))
            ttk.Label(cell, text=text, style="Legend.TLabel").pack(side="left")

    def _counter(self, parent, title):
        ttk.Label(parent, text=title, style="Legend.TLabel").pack(side="left", padx=(0, theme.SPACE_XS))
        # Fixed width, so the row does not shift as the digits grow.
        value = ttk.Label(parent, text="0", style="Step.TLabel", width=4, anchor="w")
        value.pack(side="left", padx=(0, theme.SPACE_M))
        return value

    def _bind_keys(self):
        root = self.winfo_toplevel()
        arrow_widgets = (ttk.Scale, ttk.Notebook)
        root.bind("<space>", lambda event: self._key(event, self.toggle, (ttk.Button, ttk.Checkbutton)), add="+")
        root.bind("<Right>", lambda event: self._key(event, self.single_step, arrow_widgets), add="+")
        root.bind("<Left>", lambda event: self._key(event, self.step_back, arrow_widgets), add="+")
        root.bind("r", lambda event: self._key(event, self.reset), add="+")
        # A mouse user gets the shortcuts back at once; Tab users keep focus on the control.
        focus_stage = lambda _: self.canvas.focus_set()
        # Delayed: a click on the tab ends by focusing the tab's first control, the text entry.
        self.bind("<Map>", lambda _: self.after(1, self.canvas.focus_set))
        self.canvas.bind("<Button-1>", focus_stage)
        for button in (self.play_button, self.back_button, self.step_button, self.reset_button):
            button.bind("<ButtonRelease-1>", focus_stage)

    def _key(self, event, action, native=()):
        # A focused widget that already uses the key keeps it; acting here too would fire twice.
        if self.winfo_ismapped() and not isinstance(event.widget, TEXT_INPUTS + native):
            action()

    # Data

    def generate(self):
        # After typed input the form shows TYPED_ORDER, which is not a generator.
        order = next((key for key, label in ORDERS.items() if label == self.order.get()), "random")
        kind = next(key for key, label in KINDS.items() if label == self.kind.get())
        try:
            size = self.size.get()
        except tk.TclError:
            size = 0
        if not MIN_ELEMENTS <= size <= MAX_ELEMENTS:
            self._show_error(f"El tamaño debe ser un entero entre {MIN_ELEMENTS} y {MAX_ELEMENTS}.")
            return
        self.order.set(ORDERS[order])
        values = generate_values(size, order, kind, self.rng)
        self.input_text.set(", ".join(format_value(v) if kind == "real" else str(v) for v in values))
        self._show_error("")
        self._load(values)

    def apply_input(self):
        text = self.input_text.get()
        try:
            values = parse_values(text)
        except ValueError as error:
            self._show_error(str(error))
            return
        self._show_error(decimal_comma_note(text))
        # The form must describe the array on screen, not the last generated one.
        self.size.set(len(values))
        self.kind.set(KINDS["real"] if any(isinstance(v, float) for v in values) else KINDS["int"])
        self.order.set(TYPED_ORDER)
        self._load(values)

    def _show_error(self, text):
        self.input_error.configure(text=text)
        if text:
            self.input_error.grid()
        else:
            self.input_error.grid_remove()

    def _load(self, values):
        self._cancel_timer()
        self.replay = QuicksortReplay(values)
        self.state = "idle"
        self._sync()

    # Transport

    def toggle(self):
        if self.state in ("idle", "paused"):
            # A stepped swap may still be animating; without this two timers would run.
            self._cancel_timer()
            self.state = "playing"
            self._sync_controls()
            self._advance()
        elif self.state == "playing":
            self.state = "paused"
            self._cancel_timer()
            self.draw()
            self._sync_controls()

    def step_back(self):
        if self.replay.position == 0:
            return
        self._cancel_timer()
        self.replay.seek(self.replay.position - 1)
        self.state = "paused" if self.replay.position else "idle"
        self._sync()

    def single_step(self):
        if self.state == "playing":
            self.state = "paused"
            self._cancel_timer()
            self.draw()
        elif self.state == "idle":
            self.state = "paused"
        if self.swap_start is None:
            self._apply_step()
        self._sync_controls()

    def reset(self):
        self._cancel_timer()
        self.replay.reset()
        self.state = "idle"
        self._sync()

    def _cancel_timer(self):
        if self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None
        self.swap_start = None

    def _step_ms(self):
        return theme.STEP_MS / (2 ** self.speed_exponent.get())

    def _update_speed_label(self, _=None):
        self.speed_label.configure(text=f"{2 ** self.speed_exponent.get():.3g}x")

    def _apply_step(self):
        event = self.replay.step()
        if event is None:
            return None
        if event[0] == "swap" and not self.reduce_motion.get():
            self.swap_duration = self._step_ms() * theme.SWAP_SHARE
            self.swap_start = time.perf_counter()
            self._sync_labels()
            self._animate_swap()
        else:
            self._sync()
        return event

    def _animate_swap(self):
        elapsed = (time.perf_counter() - self.swap_start) * 1000
        if elapsed >= self.swap_duration:
            self.swap_start = None
            self.timer = None
            self.draw()
            if self.state == "playing":
                self.timer = self.after(max(1, round(self._step_ms() * (1 - theme.SWAP_SHARE))), self._advance)
            return
        self.draw(theme.EASE_MOVE(elapsed / self.swap_duration))
        self.timer = self.after(theme.FRAME_MS, self._animate_swap)

    def _advance(self):
        self.timer = None
        if self.state != "playing":
            return
        event = self._apply_step()
        if self.replay.finished:
            self.state = "finished"
            self._sync_controls()
        if event is not None and self.swap_start is None and self.state == "playing":
            self.timer = self.after(round(self._step_ms()), self._advance)

    # Rendering

    def _sync(self):
        self._sync_labels()
        self.draw()

    def _sync_labels(self):
        replay = self.replay
        if replay.finished and self.state != "finished":
            self.state = "finished"
        self.narration.configure(text=replay.narration)
        self.comparisons_label.configure(text=str(replay.comparisons))
        self.swaps_label.configure(text=str(replay.swaps))
        # Counted from 1, like the experiment: the first call is level 1.
        self.depth_label.configure(text=str(max((n["depth"] + 1 for n in replay.tree), default=0)))
        self.step_label.configure(text=f"Paso {replay.position} de {replay.total}")
        self.progress.configure(value=replay.position / replay.total if replay.total else 1)
        self.code.configure(state="normal")
        self.code.tag_remove("current", "1.0", "end")
        if replay.code_line is not None:
            line = replay.code_line + 1
            self.code.tag_add("current", f"{line}.0", f"{line}.end")
            self.code.see(f"{line}.0")
        else:
            self.code.see("1.0")
        self.code.configure(state="disabled")
        self._sync_controls()

    def _sync_controls(self):
        labels = {"idle": "Iniciar", "playing": "Pausar", "paused": "Reanudar", "finished": "Iniciar"}
        finished = self.state == "finished"
        self.play_button.configure(text=labels[self.state], state="disabled" if finished else "normal")
        self.step_button.configure(state="disabled" if finished else "normal")
        self.back_button.configure(state="normal" if self.replay.position else "disabled")

    def _layout(self):
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        tree_height = height * TREE_SHARE
        bars_bottom = height - tree_height - INDEX_ROW - POINTER_ROW
        column = (width - LEFT_MARGIN - RIGHT_MARGIN) / len(self.replay.values)
        values = self.replay.values
        low = min(0, *values)
        high = max(0, *values)
        if low == high:
            high = 1
        span = high - low
        # Values that do not fit across a bar are written along it, which takes more height.
        label_length = max(self.small_font.measure(format_value(value)) for value in values)
        rotate = label_length > column - 2
        top_margin = TOP_MARGIN + (max(0, label_length + ROTATED_LABEL_GAP - FLAT_LABEL_ROOM) if rotate else 0)
        # A negative bar prints its value below the bar: keep that clear of the index row.
        negative_room = label_length + 2 * ROTATED_LABEL_GAP if rotate else NEGATIVE_LABEL_ROOM
        lowest_y = bars_bottom - (negative_room if low < 0 else 0)

        def y_of(value):
            return top_margin + (high - value) / span * (lowest_y - top_margin)

        return width, height, bars_bottom, column, y_of, rotate

    def _bar_color(self, index):
        replay = self.replay
        if replay.swapping and index in replay.swapping:
            return theme.STATE_SWAP
        if index == replay.pivot_position:
            return theme.STATE_PIVOT
        if index in replay.comparing:
            return theme.STATE_COMPARE
        if index in replay.sorted:
            return theme.STATE_SORTED
        if replay.active and not replay.active[0] <= index <= replay.active[1]:
            return theme.PLOT_BAR_DIM
        return theme.PLOT_BAR

    def draw(self, swap_progress=None):
        canvas = self.canvas
        canvas.delete("all")
        replay = self.replay
        width, height, bars_bottom, column, y_of, rotate = self._layout()
        zero = y_of(0)
        bar_width = max(column - BAR_GAP, 2)

        def x_of(index):
            return LEFT_MARGIN + column * index

        if replay.active:
            lo, hi = replay.active
            canvas.create_rectangle(x_of(lo), REGION_TOP, x_of(hi + 1), bars_bottom + INDEX_ROW,
                                    fill=theme.PLOT_REGION, outline="")

        canvas.create_line(LEFT_MARGIN, zero, width - RIGHT_MARGIN, zero, fill=theme.PLOT_GRID)
        canvas.create_text(LEFT_MARGIN - 6, zero, text="0", anchor="e", fill=theme.PLOT_TEXT_MUTED, font=self.fonts.plot)

        offsets = {}
        if swap_progress is not None and replay.swapping:
            i, j = replay.swapping
            distance = (j - i) * column * (1 - swap_progress)
            # Values are already exchanged in the replay, so the bars start from the old places.
            offsets = {i: distance, j: -distance}

        # Moving bars are drawn last so they pass in front of the others.
        indices = range(len(replay.values))
        for index in [k for k in indices if k not in offsets] + [k for k in indices if k in offsets]:
            value = replay.values[index]
            left = x_of(index) + offsets.get(index, 0)
            top, bottom = (y_of(value), zero) if value >= 0 else (zero, y_of(value))
            canvas.create_rectangle(left, top, left + bar_width, max(bottom, top + 1), fill=self._bar_color(index), outline="")
            if rotate:
                label_y, anchor = (top - ROTATED_LABEL_GAP, "w") if value >= 0 else (bottom + ROTATED_LABEL_GAP, "e")
                canvas.create_text(left + bar_width / 2, label_y, text=format_value(value), fill=theme.PLOT_TEXT,
                                   font=self.fonts.plot_small, angle=90, anchor=anchor)
            else:
                label_y = top - 10 if value >= 0 else bottom + 10
                canvas.create_text(left + bar_width / 2, label_y, text=format_value(value), fill=theme.PLOT_TEXT,
                                   font=self.fonts.plot if column > 34 else self.fonts.plot_small)
            if index in replay.candidates:
                canvas.create_rectangle(left - 1, top - 1, left + bar_width + 1, max(bottom, top + 1) + 1,
                                        outline=theme.STATE_PIVOT, width=2, dash=(4, 2))

        last_index = len(replay.values) - 1
        index_step = 2 if self.small_font.measure(str(last_index)) + 2 > column else 1
        for index in range(len(replay.values)):
            center = x_of(index) + bar_width / 2
            sorted_mark = index in replay.sorted
            if index % index_step == 0:
                canvas.create_text(center, bars_bottom + INDEX_ROW / 2 + 2, text=str(index),
                                   fill=theme.STATE_SORTED if sorted_mark else theme.PLOT_TEXT_MUTED,
                                   font=self.fonts.plot_small)
            if sorted_mark:
                # The mark that does not depend on telling the bar colours apart.
                canvas.create_line(x_of(index), bars_bottom + INDEX_ROW + 1, x_of(index) + bar_width,
                                   bars_bottom + INDEX_ROW + 1, fill=theme.STATE_SORTED, width=3)

        if replay.pivot_value is not None and replay.active:
            lo, hi = replay.active
            y = y_of(replay.pivot_value)
            canvas.create_line(x_of(lo), y, x_of(hi + 1), y, fill=theme.STATE_PIVOT, dash=(6, 3), width=2)
            # Anchored inside the plot, because a short subarray at the edge has no room of its own.
            anchor_x = max(x_of(hi + 1) - 4, LEFT_MARGIN + 110)
            label = canvas.create_text(anchor_x, PIVOT_ROW, anchor="e", fill=theme.STATE_PIVOT_TEXT,
                                       text=f"pivote = {format_value(replay.pivot_value)}", font=self.fonts.plot)
            canvas.tag_raise(label)

        self._draw_pointers(x_of, bar_width, bars_bottom)
        self._draw_split(x_of, bars_bottom)
        self._draw_tree(x_of, width, height, column)

    def _draw_pointers(self, x_of, bar_width, bars_bottom):
        canvas = self.canvas
        replay = self.replay
        y = bars_bottom + INDEX_ROW + 4
        marks = dict(replay.pointers)
        if replay.pivot_position is not None:
            marks["p"] = replay.pivot_position
        taken = {}
        for name, index in marks.items():
            if not 0 <= index < len(replay.values):
                continue
            stack = taken.get(index, 0)
            taken[index] = stack + 1
            center = x_of(index) + bar_width / 2 + stack * 13
            color = theme.STATE_PIVOT_TEXT if name == "p" else theme.STATE_COMPARE
            canvas.create_polygon(center - 4, y + 6, center + 4, y + 6, center, y, fill=color, outline="")
            canvas.create_text(center, y + 13, text=name, fill=color, font=self.fonts.plot)

    def _draw_split(self, x_of, bars_bottom):
        replay = self.replay
        if not replay.split:
            return
        lo, j, i, hi = replay.split
        y = SPLIT_LINE_ROW
        for first, last, text in ((lo, j, "<= pivote"), (i, hi, ">= pivote")):
            if first > last:
                continue
            left, right = x_of(first) + 2, x_of(last + 1) - 5
            self.canvas.create_line(left, y, right, y, fill=theme.PLOT_TEXT)
            self.canvas.create_line(left, y, left, y + 5, fill=theme.PLOT_TEXT)
            self.canvas.create_line(right, y, right, y + 5, fill=theme.PLOT_TEXT)
            if right - left > 66:
                self.canvas.create_text((left + right) / 2, SPLIT_LABEL_ROW, text=text, fill=theme.PLOT_TEXT, font=self.fonts.plot_small)

    def _draw_tree(self, x_of, width, height, column):
        canvas = self.canvas
        replay = self.replay
        top = height * (1 - TREE_SHARE) + 18
        canvas.create_line(0, top - 18, width, top - 18, fill=theme.PLOT_GRID)
        canvas.create_text(LEFT_MARGIN, top - 9, text="Árbol de recursión: una fila por nivel",
                           anchor="w", fill=theme.PLOT_TEXT_MUTED, font=self.fonts.plot_ui)
        rows = replay.max_depth + 1
        row = min(TREE_ROW_MAX, (height - top - 6) / rows)
        for depth in range(rows):
            if row >= 11:
                canvas.create_text(LEFT_MARGIN - 6, top + row * (depth + 0.5), text=str(depth + 1), anchor="e",
                                   fill=theme.PLOT_TEXT_MUTED, font=self.fonts.plot_small)
        for node in replay.tree:
            y = top + row * (node["depth"] + 0.5)
            left, right = x_of(node["lo"]) + 2, x_of(node["hi"] + 1) - 5
            if node["leaf"]:
                radius = min(3, row / 3)
                center = (left + right) / 2
                canvas.create_oval(center - radius, y - radius, center + radius, y + radius,
                                   fill=theme.STATE_SORTED, outline="")
                continue
            current = replay.active == (node["lo"], node["hi"])
            color = theme.STATE_SWAP if current else theme.PLOT_BAR
            line_width = 3 if current else 2
            canvas.create_line(left, y, right, y, fill=color, width=line_width)
            tick = min(4, row / 3)
            canvas.create_line(left, y - tick, left, y + tick, fill=color)
            canvas.create_line(right, y - tick, right, y + tick, fill=color)
