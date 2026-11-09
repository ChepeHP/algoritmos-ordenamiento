"""Turn the events of the real Quicksort into animation states. No Tk here, so it can be tested."""

import random
import re

from section1_comparison.activity2_implementation.algorithms import quicksort
from section1_comparison.activity3_experiment.experiment import median_of_three_killer

MIN_ELEMENTS = 2
MAX_ELEMENTS = 30
# Far above anything readable on a bar, and it keeps the plot's scale finite.
MAX_MAGNITUDE = 1e12

# The real lines of algorithms.py, shown beside the plot. Each event highlights one.
CODE_LINES = [
    "def _quicksort(a, lo, hi, trace):",
    "    if lo >= hi: return",
    "    pivot_index = median_of_three(a, lo, hi)",
    "    pivot = a[pivot_index]",
    "    i, j = lo, hi",
    "    while i <= j:",
    "        while a[i] < pivot: i += 1",
    "        while a[j] > pivot: j -= 1",
    "        if i <= j:",
    "            a[i], a[j] = a[j], a[i]",
    "            i += 1; j -= 1",
    "    _quicksort(a, lo, j, trace)",
    "    _quicksort(a, i, hi, trace)",
]
LINE_FOR_EVENT = {
    "range": 0, "sorted": 1, "candidates": 2, "compare_median": 2, "pivot": 3,
    "swap": 9, "partition": 11,
}

ORDERS = {
    "random": "Aleatorio",
    "sorted": "Ordenado",
    "reversed": "Inverso",
    "repeated": "Con repetidos",
    "negatives": "Con negativos",
    "adversarial": "Adversario de mediana de 3",
}
KINDS = {"int": "Enteros", "real": "Reales"}


def format_value(value):
    return f"{value:.4g}"


def parse_values(text):
    """Read the numbers typed by the user. Raises ValueError with a message for the screen."""
    parts = text.replace(";", " ").replace(",", " ").split()
    values = []
    for part in parts:
        try:
            number = float(part)
        except ValueError:
            raise ValueError(f"'{part}' no es un número. Use punto para los decimales.") from None
        if number != number or number in (float("inf"), float("-inf")):
            raise ValueError(f"'{part}' no es un número finito.")
        if abs(number) > MAX_MAGNITUDE:
            raise ValueError(f"'{part}' es demasiado grande para dibujarlo. El límite es {MAX_MAGNITUDE:.0e}.")
        values.append(int(number) if number.is_integer() and "." not in part else number)
    if not MIN_ELEMENTS <= len(values) <= MAX_ELEMENTS:
        raise ValueError(f"Escriba entre {MIN_ELEMENTS} y {MAX_ELEMENTS} números; hay {len(values)}.")
    return values


def decimal_comma_note(text):
    """A comma between digits may be a decimal comma, which parse_values reads as two numbers."""
    match = re.search(r"(\d+),(\d+)", text)
    if not match:
        return ""
    first, second = match.groups()
    return f"'{first},{second}' se leyó como dos números, {first} y {second}. Para decimales use punto."


def generate_values(n, order, kind, rng=random):
    """Build a small array for the animation."""
    if order == "random":
        values = [rng.uniform(1, 99) for _ in range(n)]
    elif order == "sorted":
        values = [(i + 1) * 90 / n for i in range(n)]
    elif order == "reversed":
        values = [(n - i) * 90 / n for i in range(n)]
    elif order == "repeated":
        values = [rng.choice([15, 40, 40, 65, 90]) for _ in range(n)]
    elif order == "negatives":
        values = [rng.uniform(-60, 60) for _ in range(n)]
    else:
        values = [(v + 1) * 90 / n for v in median_of_three_killer(n)]
    if kind == "int":
        return [round(v) for v in values]
    return [round(v, 1) for v in values]


class QuicksortReplay:
    """Applies the recorded events one by one. Every state comes from a real run of quicksort."""

    def __init__(self, values):
        self.initial = list(values)
        self.expected = list(values)
        self.events = []
        quicksort(self.expected, trace=lambda *event: self.events.append(event))
        self.reset()
        while self.step():
            pass
        self.max_depth = max((node["depth"] for node in self.tree), default=0)
        self.reset()

    def reset(self):
        self.values = list(self.initial)
        self.position = 0
        self.comparisons = 0
        self.swaps = 0
        self.active = None
        self.candidates = ()
        self.pivot_position = None
        self.pivot_value = None
        self.comparing = ()
        self.pointers = {}
        self.swapping = None
        self.split = None
        self.sorted = set()
        self.tree = []
        self._stack = []
        self.code_line = None
        self.narration = "Listo para iniciar."

    def seek(self, position):
        """Rebuild the state at an earlier step. Events only run forward, so it replays from the start."""
        self.reset()
        while self.position < position:
            self.step()

    @property
    def total(self):
        return len(self.events)

    @property
    def finished(self):
        return self.position >= self.total

    def _enter(self, lo, hi, leaf):
        while self._stack and not (self._stack[-1][0] <= lo and hi <= self._stack[-1][1]):
            self._stack.pop()
        node = {"lo": lo, "hi": hi, "depth": len(self._stack), "leaf": leaf}
        self.tree.append(node)
        if not leaf:
            self._stack.append((lo, hi))

    def _describe(self, index):
        return f"a[{index}] = {format_value(self.values[index])}"

    def step(self):
        """Apply the next event. Returns it, or None when the run is over."""
        if self.finished:
            return None
        event = self.events[self.position]
        self.position += 1
        self.comparing = ()
        self.swapping = None
        kind = event[0]
        self.code_line = LINE_FOR_EVENT.get(kind)
        handler = getattr(self, f"_on_{kind}")
        handler(*event[1:])
        if self.finished:
            self.active = None
            self.pivot_position = None
            self.pivot_value = None
            self.pointers = {}
            self.split = None
            self.candidates = ()
            self.code_line = None
            self.narration = (
                f"Ordenado con {self.comparisons} comparaciones y {self.swaps} intercambios. Reiniciar lo repite."
            )
        return event

    def _on_range(self, lo, hi):
        self.active = (lo, hi)
        self.candidates = ()
        self.pivot_position = None
        self.pivot_value = None
        self.pointers = {}
        self.split = None
        self._enter(lo, hi, leaf=False)
        self.narration = f"Nueva llamada recursiva: se ordena a[{lo}..{hi}]."

    def _on_candidates(self, lo, mid, hi):
        self.candidates = (lo, mid, hi)
        self.narration = (
            f"Mediana de 3: candidatos {self._describe(lo)}, {self._describe(mid)} y {self._describe(hi)}."
        )

    def _on_compare_median(self, x, y):
        self.comparisons += 1
        self.comparing = (x, y)
        answer = "sí" if self.values[x] < self.values[y] else "no"
        self.narration = f"Mediana de 3: ¿{self._describe(x)} < {self._describe(y)}? {answer}."

    def _on_pivot(self, index):
        self.pivot_position = index
        self.pivot_value = self.values[index]
        self.candidates = ()
        self.narration = f"El pivote es {self._describe(index)}, la mediana de los tres candidatos."

    def _on_compare(self, index, pointer):
        self.comparisons += 1
        self.comparing = (index,)
        self.pointers[pointer] = index
        value = self.values[index]
        pivot = format_value(self.pivot_value)
        if pointer == "i":
            self.code_line = 6
            advances = value < self.pivot_value
            question = f"¿{self._describe(index)} < {pivot}?"
            result = "sí, i avanza" if advances else "no, i se detiene"
        else:
            self.code_line = 7
            advances = value > self.pivot_value
            question = f"¿{self._describe(index)} > {pivot}?"
            result = "sí, j retrocede" if advances else "no, j se detiene"
        self.narration = f"{question} {result}."

    def _on_swap(self, i, j):
        self.narration = f"Intercambio de {self._describe(i)} con {self._describe(j)}."
        self.values[i], self.values[j] = self.values[j], self.values[i]
        self.swaps += 1
        self.swapping = (i, j)
        if self.pivot_position == i:
            self.pivot_position = j
        elif self.pivot_position == j:
            self.pivot_position = i

    def _on_partition(self, lo, j, i, hi):
        self.split = (lo, j, i, hi)
        self.pointers = {"i": i, "j": j} if lo <= j or i <= hi else {}
        self.narration = (
            f"Partición lista: a[{lo}..{j}] <= {format_value(self.pivot_value)} <= a[{i}..{hi}]."
        )

    def _on_sorted(self, first, last):
        self.sorted.update(range(first, last + 1))
        if first == last:
            self._enter(first, last, leaf=True)
            self.narration = f"{self._describe(first)} ya está en su posición final."
        else:
            self.narration = f"a[{first}..{last}] son iguales al pivote y ya están en su posición final."
