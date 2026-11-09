"""Build the results report PDF from the saved CSV files. Needs pdflatex. Run from the project root:

    python -m section3_deliverables.build_results_report

Every number in the tables and in the text comes from section3_deliverables/data.
"""

import csv
import math
import re
import subprocess
import tempfile
from pathlib import Path
from statistics import median

from section1_comparison.activity3_experiment.experiment import (
    CONFIG_LABELS,
    COUNT_REPETITIONS,
    COUNT_SIZES,
    DEFAULT_REPETITIONS,
    DEFAULT_SIZES,
    THEORY,
    fit_slope,
)

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
AUTHOR = "Héctor Manuel Salazar Rivera"
ALGORITHMS = ("Bubble Sort", "Quicksort")
LARGE_FROM = 2000


def read(name):
    with open(DATA / name, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


summary = read("timings_summary.csv")
operations = read("operation_counts.csv")
environment = dict(line.split("=", 1) for line in (DATA / "environment.txt").read_text(encoding="utf-8").splitlines())
SECONDS = {(r["algorithm"], r["config"], int(r["n"])): float(r["median_s"]) for r in summary}
CV = {(r["algorithm"], r["config"], int(r["n"])): float(r["stdev_s"]) / float(r["mean_s"]) for r in summary}


def count(algorithm, config, n, field):
    return median(int(r[field]) for r in operations
                  if r["algorithm"] == algorithm and r["config"] == config and int(r["n"]) == n)


def ms(value):
    value *= 1000
    return f"{value:.0f}" if value >= 1000 else f"{value:.3g}"


def integer(value):
    return f"{value:,.0f}".replace(",", "\\,")


def times_table(algorithm):
    head = " & ".join(["Configuración"] + [f"{n}" for n in DEFAULT_SIZES])
    rows = [" & ".join([label] + [ms(SECONDS[algorithm, config, n]) for n in DEFAULT_SIZES]) + r" \\"
            for config, label in CONFIG_LABELS.items()]
    return "\n".join([r"\begin{tabular}{l" + "r" * len(DEFAULT_SIZES) + "}", r"\toprule", head + r" \\", r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"])


def ratio_table():
    head = " & ".join(["Configuración"] + [f"{n}" for n in DEFAULT_SIZES])
    rows = []
    for config, label in CONFIG_LABELS.items():
        cells = [SECONDS["Bubble Sort", config, n] / SECONDS["Quicksort", config, n] for n in DEFAULT_SIZES]
        rows.append(" & ".join([label] + [f"{c:.3g}" if c < 100 else f"{c:.0f}" for c in cells]) + r" \\")
    return "\n".join([r"\begin{tabular}{l" + "r" * len(DEFAULT_SIZES) + "}", r"\toprule", head + r" \\", r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"])


def slope(algorithm, config, smallest):
    sizes = [n for n in DEFAULT_SIZES if n >= smallest]
    return fit_slope(sizes, [SECONDS[algorithm, config, n] for n in sizes])


def theory_slope(algorithm, config, smallest):
    sizes = [n for n in DEFAULT_SIZES if n >= smallest]
    growth = THEORY[algorithm, config][0]
    return fit_slope(sizes, [growth(n) for n in sizes])[0]


def fits_table():
    tex_theory = {"n": "$n$", "n log n": r"$n \log n$", "n^2": "$n^2$"}
    rows = []
    for algorithm in ALGORITHMS:
        for config, label in CONFIG_LABELS.items():
            growth, theory = THEORY[algorithm, config]
            whole, r_squared = slope(algorithm, config, DEFAULT_SIZES[0])
            large, _ = slope(algorithm, config, LARGE_FROM)
            last, previous = DEFAULT_SIZES[-1], DEFAULT_SIZES[-2]
            doubling = SECONDS[algorithm, config, last] / SECONDS[algorithm, config, previous]
            expected = growth(last) / growth(previous)
            rows.append(" & ".join([
                algorithm, label, tex_theory[theory], f"{whole:.2f}", f"{large:.2f}",
                f"{theory_slope(algorithm, config, LARGE_FROM):.2f}", f"{r_squared:.3f}", f"{doubling:.2f}", f"{expected:.2f}",
            ]) + r" \\")
    head = r"Algoritmo & Configuración & Teoría & $k$ todo & $k$ grande & $k$ teórica & $R^2$ & $T(2n)/T(n)$ & teórica \\"
    return "\n".join([r"\begin{tabular}{llrrrrrrr}", r"\toprule", head, r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"])


def operations_table():
    n = COUNT_SIZES[-1]
    rows = []
    for config, label in CONFIG_LABELS.items():
        rows.append(" & ".join([
            label,
            integer(count("Bubble Sort", config, n, "comparisons")),
            integer(count("Bubble Sort", config, n, "swaps")),
            integer(count("Quicksort", config, n, "comparisons")),
            integer(count("Quicksort", config, n, "swaps")),
            integer(count("Quicksort", config, n, "max_recursion_depth")),
        ]) + r" \\")
    return "\n".join([
        r"\begin{tabular}{lrrrrr}", r"\toprule",
        r" & \multicolumn{2}{c}{Bubble Sort} & \multicolumn{3}{c}{Quicksort} \\",
        r"Configuración & Comparaciones & Intercambios & Comparaciones & Intercambios & Profundidad \\",
        r"\midrule", *rows, r"\bottomrule", r"\end{tabular}",
    ])


def slope_range(algorithm, configs, smallest):
    values = [slope(algorithm, config, smallest)[0] for config in configs]
    return f"{min(values):.2f}", f"{max(values):.2f}"


QUADRATIC = ("random", "random_int", "reversed", "repeated", "adversarial")
LOG_LINEAR = ("random", "random_int", "sorted", "reversed", "repeated")
LAST, BIG_COUNT = DEFAULT_SIZES[-1], COUNT_SIZES[-1]
log_big = BIG_COUNT * math.log2(BIG_COUNT)
worst_cv = max(CV, key=CV.get)
worst_large_cv = max((key for key in CV if key[2] >= LARGE_FROM), key=CV.get)
whole_low, whole_high = slope_range("Bubble Sort", QUADRATIC, DEFAULT_SIZES[0])
large_low, large_high = slope_range("Bubble Sort", QUADRATIC, LARGE_FROM)
quick_low, quick_high = slope_range("Quicksort", LOG_LINEAR, DEFAULT_SIZES[0])


def ns_per_comparison(n):
    return SECONDS["Bubble Sort", "random", n] / count("Bubble Sort", "random", n, "comparisons") * 1e9


VALUES = {
    "AUTHOR": AUTHOR,
    "SIZES": ", ".join(str(n) for n in DEFAULT_SIZES),
    "REPS": str(DEFAULT_REPETITIONS),
    "COUNT_SIZES": ", ".join(str(n) for n in COUNT_SIZES),
    "COUNT_REPS": str(COUNT_REPETITIONS),
    "SEED": environment["seed"],
    "PYTHON": f"{environment['implementation']} {environment['python']}",
    "SYSTEM": f"{environment['system']}, {environment['machine']}".replace("_", r"\_"),
    "TOTAL_MIN": f"{int(environment['total_seconds']) / 60:.0f}",
    "TOTAL_S": environment["total_seconds"],
    "LAST": str(LAST),
    "BIGN": str(BIG_COUNT),
    "LARGE_FROM": str(LARGE_FROM),
    "RUNS": str(len(CONFIG_LABELS) * len(DEFAULT_SIZES) * DEFAULT_REPETITIONS * 2),
    "WORST_CV": f"{CV[worst_cv]:.2f}",
    "WORST_CV_US": f"{SECONDS[worst_cv] * 1e6:.0f}",
    "WORST_CV_N": str(worst_cv[2]),
    "WORST_LARGE_CV": f"{CV[worst_large_cv]:.3f}",
    "B_RANDOM_S": f"{SECONDS['Bubble Sort', 'random', LAST]:.2f}",
    "Q_RANDOM_MS": ms(SECONDS["Quicksort", "random", LAST]),
    "RATIO_RANDOM": f"{SECONDS['Bubble Sort', 'random', LAST] / SECONDS['Quicksort', 'random', LAST]:.0f}",
    "RATIO_REPEATED": f"{SECONDS['Bubble Sort', 'repeated', LAST] / SECONDS['Quicksort', 'repeated', LAST]:.0f}",
    "B_REV_S": f"{SECONDS['Bubble Sort', 'reversed', LAST]:.2f}",
    "Q_REV_MS": ms(SECONDS["Quicksort", "reversed", LAST]),
    "RATIO_REV": f"{SECONDS['Bubble Sort', 'reversed', LAST] / SECONDS['Quicksort', 'reversed', LAST]:.0f}",
    "REV_OVER_RANDOM": f"{SECONDS['Bubble Sort', 'reversed', LAST] / SECONDS['Bubble Sort', 'random', LAST]:.2f}",
    "B_SORT_MS": ms(SECONDS["Bubble Sort", "sorted", LAST]),
    "Q_SORT_MS": ms(SECONDS["Quicksort", "sorted", LAST]),
    "SORT_ADV": f"{SECONDS['Quicksort', 'sorted', LAST] / SECONDS['Bubble Sort', 'sorted', LAST]:.1f}",
    "B_ADV_S": f"{SECONDS['Bubble Sort', 'adversarial', LAST]:.2f}",
    "Q_ADV_S": f"{SECONDS['Quicksort', 'adversarial', LAST]:.2f}",
    "RATIO_ADV": f"{SECONDS['Bubble Sort', 'adversarial', LAST] / SECONDS['Quicksort', 'adversarial', LAST]:.1f}",
    "ADV_OVER_RANDOM": f"{SECONDS['Quicksort', 'adversarial', LAST] / SECONDS['Quicksort', 'random', LAST]:.0f}",
    "RATIO_250": f"{SECONDS['Bubble Sort', 'random', 250] / SECONDS['Quicksort', 'random', 250]:.1f}",
    "WHOLE_LOW": whole_low, "WHOLE_HIGH": whole_high,
    "LARGE_LOW": large_low, "LARGE_HIGH": large_high,
    "QUICK_LOW": quick_low, "QUICK_HIGH": quick_high,
    "Q_THEORY_WHOLE": f"{theory_slope('Quicksort', 'random', DEFAULT_SIZES[0]):.2f}",
    "B_SORT_SLOPE": f"{slope('Bubble Sort', 'sorted', DEFAULT_SIZES[0])[0]:.2f}",
    "B_SORT_SLOPE_LARGE": f"{slope('Bubble Sort', 'sorted', LARGE_FROM)[0]:.2f}",
    "Q_ADV_SLOPE": f"{slope('Quicksort', 'adversarial', DEFAULT_SIZES[0])[0]:.2f}",
    "NS_SMALL": f"{ns_per_comparison(COUNT_SIZES[0]):.0f}",
    "NS_LARGE": f"{ns_per_comparison(BIG_COUNT):.0f}",
    "BUB_SORT_COMP": integer(count("Bubble Sort", "sorted", BIG_COUNT, "comparisons")),
    "BUB_REV_COMP": integer(count("Bubble Sort", "reversed", BIG_COUNT, "comparisons")),
    "BUB_REV_SWAP": integer(count("Bubble Sort", "reversed", BIG_COUNT, "swaps")),
    "BUB_RANDOM_COMP": integer(count("Bubble Sort", "random", BIG_COUNT, "comparisons")),
    "BUB_RANDOM_SWAP": integer(count("Bubble Sort", "random", BIG_COUNT, "swaps")),
    "BUB_FORMULA": integer(BIG_COUNT * (BIG_COUNT - 1) / 2),
    "BUB_QUARTER": integer(BIG_COUNT * (BIG_COUNT - 1) / 4),
    "BUB_ADV_COMP": integer(count("Bubble Sort", "adversarial", BIG_COUNT, "comparisons")),
    "BUB_ADV_SWAP": integer(count("Bubble Sort", "adversarial", BIG_COUNT, "swaps")),
    "Q_SORT_COMP": integer(count("Quicksort", "sorted", BIG_COUNT, "comparisons")),
    "Q_SORT_DEPTH": integer(count("Quicksort", "sorted", BIG_COUNT, "max_recursion_depth")),
    "Q_REV_COMP": integer(count("Quicksort", "reversed", BIG_COUNT, "comparisons")),
    "Q_REV_DEPTH": integer(count("Quicksort", "reversed", BIG_COUNT, "max_recursion_depth")),
    "Q_REV_SWAP": integer(count("Quicksort", "reversed", BIG_COUNT, "swaps")),
    "Q_RANDOM_COMP": integer(count("Quicksort", "random", BIG_COUNT, "comparisons")),
    "Q_RANDOM_SWAP": integer(count("Quicksort", "random", BIG_COUNT, "swaps")),
    "Q_RANDOM_DEPTH": integer(count("Quicksort", "random", BIG_COUNT, "max_recursion_depth")),
    "Q_REPEATED_SWAP": integer(count("Quicksort", "repeated", BIG_COUNT, "swaps")),
    "Q_REPEATED_DEPTH": integer(count("Quicksort", "repeated", BIG_COUNT, "max_recursion_depth")),
    "Q_ADV_COMP": integer(count("Quicksort", "adversarial", BIG_COUNT, "comparisons")),
    "Q_ADV_DEPTH": integer(count("Quicksort", "adversarial", BIG_COUNT, "max_recursion_depth")),
    "LOG_BIG": integer(log_big),
    "LOG2_BIG": f"{math.log2(BIG_COUNT):.1f}",
    "FACTOR_SORT": f"{count('Quicksort', 'sorted', BIG_COUNT, 'comparisons') / log_big:.2f}",
    "FACTOR_RANDOM": f"{count('Quicksort', 'random', BIG_COUNT, 'comparisons') / log_big:.2f}",
    "N2_QUARTER": integer(BIG_COUNT ** 2 / 4),
    "N2_HALF": integer(BIG_COUNT ** 2 / 2),
    "EXAM_VS_MEASURED": f"{(BIG_COUNT ** 2 / 2) / count('Quicksort', 'reversed', BIG_COUNT, 'comparisons'):.0f}",
    "TABLE_BUBBLE": times_table("Bubble Sort"),
    "TABLE_QUICK": times_table("Quicksort"),
    "TABLE_RATIO": ratio_table(),
    "TABLE_FITS": fits_table(),
    "TABLE_OPS": operations_table(),
    "CHARTS": str(HERE / "charts") + "/",
}

TEMPLATE = r"""
\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.4cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[spanish,es-nodecimaldot,es-tabla]{babel}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{float}
\usepackage[font=small,labelfont=bf]{caption}
\usepackage[hidelinks]{hyperref}
\graphicspath{{@CHARTS@}}
\setlength{\parskip}{0.5em}
\setlength{\parindent}{0pt}
\title{Resultados experimentales: Bubble Sort y Quicksort}
\author{@AUTHOR@\\Optimización y Métodos Computacionales}
\date{Noviembre de 2026}
\begin{document}
\maketitle

\section{Alcance}
Este documento reúne la metodología, los casos de prueba, las gráficas y la interpretación del punto 3 de los entregables. El análisis formal está en \path{section1_comparison/activity1_formal_analysis/}: el PDF del examen y un anexo que añade la terminación de los dos algoritmos, la corrección de Quicksort y el análisis del pivote por mediana de 3. Los datos completos están en \path{section3_deliverables/data/} y las gráficas en \path{section3_deliverables/charts/}. Las tablas y las cifras de este texto se generan desde esos archivos con \path{section3_deliverables/build_results_report.py}.

\section{Implementación evaluada}
Ambos algoritmos están en \path{section1_comparison/activity2_implementation/algorithms.py} y no usan funciones de ordenamiento de Python. Una prueba revisa que el código no las llame.

\textbf{Bubble Sort} es iterativo y termina antes si una pasada no hace intercambios. Esa salida temprana produce el mejor caso de $n-1$ comparaciones que da el examen. El pseudocódigo del examen no la incluye: sin ella, un arreglo ordenado también haría $n(n-1)/2$ comparaciones.

\textbf{Quicksort} es recursivo y parte el arreglo con dos punteros, $i$ y $j$, que avanzan el uno hacia el otro y se detienen en elementos iguales al pivote. El pivote es la mediana de los elementos en las posiciones $lo$, $\lfloor(lo+hi)/2\rfloor$ y $hi$.

\section{Elección del pivote: mediana de 3}
El examen analiza como peor caso un arreglo inverso con el último elemento como pivote: cada partición deja un lado vacío y $T(n)=T(n-1)+cn$, es decir $\Theta(n^2)$. Con $n=@BIGN@$, eso significa unas $n^2/2=@N2_HALF@$ comparaciones. Esta cifra sale de la fórmula del examen y no se midió, porque el programa no implementa ese pivote.

Con mediana de 3, en un arreglo ordenado o inverso el elemento central es la mediana exacta, y ese caso se vuelve el mejor. Con $n=@BIGN@$ e inverso se midieron @Q_REV_COMP@ comparaciones, unas @EXAM_VS_MEASURED@ veces menos, y una profundidad de @Q_REV_DEPTH@, igual a $\log_2 n$ redondeado. El costo es de 2 o 3 comparaciones adicionales por llamada.

La mediana de 3 no elimina el caso cuadrático, solo hace que sea difícil encontrarlo por accidente. Para comprobarlo, el experimento incluye una entrada construida con el adversario de McIlroy (1999), que decide el orden de los valores durante las comparaciones para perjudicar siempre al pivote. Con esa entrada Quicksort crece como $n^2$ y su profundidad llega a @Q_ADV_DEPTH@ con $n=@BIGN@$, cerca de $n/2$. Se prefirió la mediana de 3 frente a un pivote aleatorio porque es determinista: la misma entrada da siempre la misma ejecución, lo que permite repetir los experimentos y reproducir esa ejecución en la animación.

\section{Metodología}
\textbf{Tamaños.} $n$ = @SIZES@. Al duplicar el tamaño en cada paso, la razón $T(2n)/T(n)$ se lee directamente: cerca de 4 para $n^2$ y cerca de 2 para $n$ o $n\log n$. Los puntos también quedan a igual distancia en un eje logarítmico. Por debajo de 250 los tiempos más cortos se acercan al ruido de medición: Bubble Sort sobre un arreglo ordenado con $n=250$ ya tarda menos de 5 microsegundos. El tope es @LAST@ porque ahí Bubble Sort ya tarda entre 4 y 7 s por corrida y el experimento completo toma unos @TOTAL_MIN@ minutos. Duplicar el tamaño una vez más cuadruplicaría el tiempo de Bubble Sort.

\textbf{Repeticiones.} @REPS@ por combinación, para un total de @RUNS@ corridas cronometradas. Se reporta la mediana porque una interrupción del sistema operativo solo puede alargar una corrida y la mediana no se deja arrastrar por ese valor. El número es impar para que la mediana sea una medición real. La dispersión justifica este número: desde $n=@LARGE_FROM@$ el coeficiente de variación más alto es @WORST_LARGE_CV@. El más alto de todo el experimento es @WORST_CV@, en una corrida de unos @WORST_CV_US@ microsegundos ($n=@WORST_CV_N@$).

\textbf{Configuraciones.} Aleatorio con reales, aleatorio con enteros, ordenado, inverso, muy repetidos (10 valores distintos) y adversario de mediana de 3. El enunciado pide aleatorio, ordenado e inverso. Los repetidos y el adversario se agregaron para ver los límites del pivote.

\textbf{Control de la medición.} En \path{section1_comparison/activity3_experiment/experiment.py}, la función \texttt{measure} cronometra solo la llamada al algoritmo con \texttt{time.perf\_counter}. Los datos se generan antes y se copian fuera del cronómetro. La interfaz no participa: los datos guardados vienen de \path{run_experiment.py}, que corre sin ventana. Los dos algoritmos reciben el mismo arreglo en cada repetición, y su orden se alterna para que ninguno aproveche siempre la memoria caché que deja el otro. El recolector de basura se ejecuta antes de cada corrida y queda apagado durante ella. La semilla es @SEED@.

\textbf{Conteo de operaciones.} Las comparaciones, los intercambios y la profundidad se cuentan en corridas aparte, sin cronómetro, porque contar agrega costo. Se usan los tamaños @COUNT_SIZES@ con @COUNT_REPS@ repeticiones, y se reporta la mediana.

\textbf{Equipo.} @PYTHON@ en @SYSTEM@. El experimento completo tardó @TOTAL_S@ s. El archivo \path{environment.txt} no registró el modelo del procesador.

\section{Casos de prueba}
Las pruebas están en \path{section1_comparison/activity2_implementation/test_algorithms.py} y \path{section2_animation/test_replay.py}. Son 26 y pasan todas con el comando que indica el README. Cubren:
\begin{itemize}
\item Arreglos fijos con enteros, reales, mezcla de ambos, repetidos, negativos y todos iguales, además de ordenado, inverso, vacío, un elemento, dos elementos y tres casos de 5000 elementos. Cada resultado se revisa: debe quedar ordenado y conservar los mismos elementos.
\item 500 listas aleatorias con enteros y reales mezclados, por algoritmo.
\item La mediana de 3 en cada orden posible de tres valores, y la división por la mitad en arreglos ordenados e inversos.
\item Las fórmulas del examen: $n-1$ comparaciones en Bubble Sort ordenado y $n(n-1)/2$ en inverso.
\item La fidelidad de la animación: los eventos que dibuja reproducen el resultado real, y sus contadores coinciden con un conteo independiente.
\end{itemize}

\section{Resultados}
\begin{table}[H]\centering\small
\caption{Bubble Sort: mediana del tiempo en milisegundos, por tamaño $n$.}
@TABLE_BUBBLE@
\end{table}
\begin{table}[H]\centering\small
\caption{Quicksort: mediana del tiempo en milisegundos, por tamaño $n$.}
@TABLE_QUICK@
\end{table}
\begin{table}[H]\centering\small
\caption{Cuántas veces tarda más Bubble Sort que Quicksort, por tamaño $n$. Un valor menor que 1 indica que Bubble Sort es más rápido.}
@TABLE_RATIO@
\end{table}
\begin{table}[H]\centering\footnotesize
\caption{Ajuste $T(n)=c\,n^k$ por mínimos cuadrados en escala log-log. La columna $k$ todo usa todos los tamaños; $k$ grande y $k$ teórica usan $n\ge @LARGE_FROM@$. La razón $T(2n)/T(n)$ compara $n=@LAST@$ con $n=8000$. $R^2$ corresponde al ajuste con todos los tamaños.}
\resizebox{\textwidth}{!}{@TABLE_FITS@}
\end{table}
\begin{table}[H]\centering\small
\caption{Operaciones contadas con $n=@BIGN@$ (mediana de @COUNT_REPS@ repeticiones).}
\resizebox{\textwidth}{!}{@TABLE_OPS@}
\end{table}

\begin{figure}[H]\centering\includegraphics[width=\textwidth]{01_time_vs_n_loglog.png}
\caption{Tiempo contra tamaño en escala log-log. La línea punteada es la curva teórica con su constante ajustada a las mediciones. La banda va del mínimo al máximo. Solo en el panel del adversario las dos curvas tienen la misma complejidad teórica, $n^2$.}
\end{figure}
\begin{figure}[H]\centering\includegraphics[width=\textwidth]{02_time_vs_n_linear.png}
\caption{Arreglo aleatorio en escala lineal. Con $n=@LAST@$, Bubble Sort tarda @B_RANDOM_S@ s y Quicksort @Q_RANDOM_MS@ ms, tan poco que su curva casi no se separa de cero.}
\end{figure}
\begin{figure}[H]\centering\includegraphics[width=\textwidth]{03_speed_ratio.png}
\caption{Razón de tiempos. Crece con $n$ en cuatro paneles. En ordenado está por debajo de 1 y en el adversario se estabiliza cerca de @RATIO_ADV@.}
\end{figure}
\begin{figure}[H]\centering\includegraphics[width=\textwidth]{04_time_over_theory.png}
\caption{Tiempo dividido entre la curva teórica ajustada. Una curva plana indica el crecimiento esperado. Bubble Sort sube en los tamaños pequeños y se aplana desde $n=@LARGE_FROM@$ aproximadamente.}
\end{figure}
\begin{figure}[H]\centering\includegraphics[width=\textwidth]{05_comparisons.png}
\caption{Comparaciones contadas. Las líneas punteadas de Bubble Sort son las fórmulas del examen: $n-1$ en ordenado y, como máximo, $n(n-1)/2$ en los demás. Las de Quicksort tienen la constante ajustada.}
\end{figure}
\begin{figure}[H]\centering\includegraphics[width=\textwidth]{06_swaps.png}
\caption{Intercambios contados. En un arreglo ordenado ninguno de los dos intercambia. El eje es logarítmico salvo cerca de cero, para poder mostrar ese valor.}
\end{figure}
\begin{figure}[H]\centering\includegraphics[width=\textwidth]{07_recursion_depth.png}
\caption{Profundidad máxima de recursión de Quicksort. En ordenado e inverso coincide con $\log_2 n$; en aleatorio es cerca del doble; en el adversario coincide con $n/2$.}
\end{figure}

\section{Teoría contra medición}
\textbf{Bubble Sort, conteos.} Coinciden exactamente con el examen. Con $n=@BIGN@$: @BUB_SORT_COMP@ comparaciones en ordenado, que es $n-1$, y @BUB_REV_COMP@ comparaciones e intercambios en inverso, que es $n(n-1)/2$. En aleatorio hay @BUB_RANDOM_COMP@ comparaciones, un poco menos que @BUB_FORMULA@ por la salida temprana, y @BUB_RANDOM_SWAP@ intercambios, cerca de $n(n-1)/4=@BUB_QUARTER@$, que es el número esperado de inversiones de una permutación aleatoria.

\textbf{Bubble Sort, tiempos.} Con todos los tamaños, la pendiente en los casos cuadráticos va de @WHOLE_LOW@ a @WHOLE_HIGH@, por encima del 2 teórico. El exceso viene de los tamaños pequeños. Con $n\ge @LARGE_FROM@$ la pendiente baja a un rango de @LARGE_LOW@ a @LARGE_HIGH@. Los conteos sí crecen como $n^2$, así que lo que cambia es el costo de cada operación: en aleatorio, el tiempo por comparación sube de unos @NS_SMALL@ ns con $n=250$ a unos @NS_LARGE@ ns con $n=@BIGN@$. La causa probable es la memoria caché, porque un arreglo mayor deja de caber en los niveles rápidos. Esto no se midió, así que queda como hipótesis.

\textbf{Bubble Sort, ordenado.} La pendiente es @B_SORT_SLOPE@ con todos los tamaños y @B_SORT_SLOPE_LARGE@ con $n\ge @LARGE_FROM@$, frente a 1 en teoría. Aquí los tiempos pequeños son de pocos microsegundos y pesa más el ruido.

\textbf{Quicksort, conteos.} La recurrencia del mejor caso del examen predice unas $n\log_2 n=@LOG_BIG@$ comparaciones con $n=@BIGN@$. En ordenado se contaron @Q_SORT_COMP@, un factor de @FACTOR_SORT@. En aleatorio se contaron @Q_RANDOM_COMP@, un factor de @FACTOR_RANDOM@, porque las particiones no son exactas: la profundidad es @Q_RANDOM_DEPTH@, frente a @LOG2_BIG@ de $\log_2 n$. El orden de crecimiento se conserva, pero la constante es mayor.

\textbf{Quicksort, tiempos.} La pendiente en los casos no adversarios va de @QUICK_LOW@ a @QUICK_HIGH@, cerca de la pendiente de @Q_THEORY_WHOLE@ que tiene $n\log_2 n$ en este rango. Una pendiente mayor que 1 es lo que se espera del factor logarítmico. Con el adversario la pendiente es @Q_ADV_SLOPE@ y las comparaciones son @Q_ADV_COMP@, cerca de $n^2/4=@N2_QUARTER@$. Este valor es la mitad de las $n^2/2$ del peor caso del examen, lo que concuerda con una profundidad de $n/2$: cada nivel descarta unos dos elementos en lugar de uno.

\textbf{Lo que la notación asintótica no predice.} Dos configuraciones con la misma complejidad pueden diferir mucho:
\begin{itemize}
\item Bubble Sort inverso tarda @REV_OVER_RANDOM@ veces lo que tarda aleatorio, porque intercambia en cada comparación (@BUB_REV_SWAP@ intercambios frente a @BUB_RANDOM_SWAP@).
\item Bubble Sort con la entrada adversaria tarda menos que con aleatorio (@B_ADV_S@ s frente a @B_RANDOM_S@ s). Esa entrada solo perjudica a Quicksort. Bubble Sort hace menos comparaciones (@BUB_ADV_COMP@) y menos intercambios (@BUB_ADV_SWAP@).
\item Quicksort inverso tarda la mitad que aleatorio (@Q_REV_MS@ ms frente a @Q_RANDOM_MS@ ms), con particiones exactas y solo @Q_REV_SWAP@ intercambios frente a @Q_RANDOM_SWAP@.
\item Con muchos repetidos, Quicksort hace más intercambios (@Q_REPEATED_SWAP@) porque los punteros se detienen en los iguales, y a cambio la profundidad baja a @Q_REPEATED_DEPTH@.
\end{itemize}

\textbf{Profundidad en la animación.} El contador de la animación cuenta las llamadas que hacen trabajo. Por eso puede dar 1 menos que este experimento, que también cuenta las llamadas que regresan de inmediato.

\section{Cuándo conviene cada algoritmo}
\textbf{Quicksort} ganó en todas las configuraciones menos la ordenada. Su ventaja crece con $n$, salvo con el adversario, donde se estabiliza. Con $n=@LAST@$ fue @RATIO_RANDOM@ veces más rápido en aleatorio, @RATIO_REV@ veces en inverso y @RATIO_REPEATED@ veces con repetidos. Ya con $n=250$, el menor tamaño medido, la ventaja en aleatorio es de @RATIO_250@ veces. Su límite es la entrada adversaria: tarda @ADV_OVER_RANDOM@ veces más que en aleatorio, aunque sigue siendo @RATIO_ADV@ veces más rápido que Bubble Sort. Además usa pila de recursión, de $\Theta(\log n)$ en el mejor caso hasta $\Theta(n)$ en el peor. Con la entrada adversaria hubo que subir el límite de recursión de Python.

\textbf{Bubble Sort} solo ganó con el arreglo ya ordenado: @B_SORT_MS@ ms frente a @Q_SORT_MS@ ms con $n=@LAST@$, unas @SORT_ADV@ veces más rápido, y sin escribir nada. Su memoria adicional es $O(1)$. Fuera de ese caso, la medición no lo favorece en ningún tamaño desde $n=250$.

\section{Limitaciones}
\begin{itemize}
\item Todo se midió en un solo equipo, con un intérprete de Python. Los tiempos absolutos no se trasladan a otra máquina; las pendientes y razones son más estables.
\item No se midieron arreglos casi ordenados ni tamaños menores que 250, así que este informe no afirma nada medido sobre ellos.
\item La memoria no se midió directamente. La profundidad de recursión es la única medida relacionada.
\item Las configuraciones ordenado, inverso y adversario son deterministas: sus repeticiones miden solo el ruido del equipo, no distintas entradas.
\end{itemize}

\section*{Referencia}
McIlroy, M. D. (1999). A killer adversary for quicksort. \textit{Software: Practice and Experience}, 29(4), 341-344.

\end{document}
"""


def main():
    text = TEMPLATE
    for key, value in VALUES.items():
        text = text.replace(f"@{key}@", value)
    leftover = re.findall(r"@[A-Z_0-9]+@", text)
    assert not leftover, f"unfilled placeholders: {leftover}"
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "resultados_experimentales.tex"
        source.write_text(text, encoding="utf-8")
        for _ in range(2):
            run = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", source.name],
                                 cwd=folder, capture_output=True, text=True, errors="replace")
            if run.returncode:
                raise SystemExit(run.stdout[-3000:])
        output = HERE / "resultados_experimentales.pdf"
        output.write_bytes((Path(folder) / "resultados_experimentales.pdf").read_bytes())
    print(output)


if __name__ == "__main__":
    main()
