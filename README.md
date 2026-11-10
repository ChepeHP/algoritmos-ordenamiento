# Análisis y visualización de algoritmos de ordenamiento

Aplicación de escritorio en Python que compara Bubble Sort y Quicksort con experimentos de tiempo y anima Quicksort paso a paso. Quicksort usa la mediana de 3 como pivote. El enunciado está en `brief/sorting_algorithms.pdf`.

## Instalación

Se probó con Python 3.14.8, Matplotlib 3.11.2 y NumPy 2.5.4 . Tkinter viene con Python en la mayoría de instalaciones; en algunas distribuciones de Linux hay que instalarlo aparte, por ejemplo con `sudo apt install python3-tk`.

```
pip install -r requirements.txt
```

En Windows, Python se instala desde python.org. En el instalador hay que marcar "Add python.exe to PATH" y dejar marcada la opción "tcl/tk and IDLE", que instala Tkinter. Los comandos de este archivo se escriben en PowerShell, abierta en la carpeta del proyecto.

## Ejecución

Desde la carpeta raíz del proyecto:

```
python main.py
```

La ventana tiene dos pestañas:

- **Comparar algoritmos:** abre con los resultados guardados del experimento completo. Permite elegir tamaños, repeticiones y configuraciones, correr un experimento nuevo y guardar sus datos y gráficas.
- **Animar Quicksort:** recibe entre 2 y 30 números, escritos o generados. Se separan con comas, punto y coma o espacios, y los decimales llevan punto, por ejemplo `5, -2, 3.5, 3`. Permite iniciar, pausar, reanudar, avanzar, retroceder, reiniciar y cambiar la velocidad. Teclado: Espacio inicia o pausa, las flechas avanzan o retroceden un paso, R reinicia.

## Otros comandos

Todos se ejecutan desde la carpeta raíz.

| Qué hace | Comando |
|---|---|
| Correr las pruebas | `python -m unittest section1_comparison.activity2_implementation.test_algorithms section2_animation.test_replay` |
| Repetir el experimento completo (unos 7 minutos; reemplaza los CSV) | `python -m section1_comparison.activity3_experiment.run_experiment` |
| Regenerar las gráficas desde los CSV | `python -m section1_comparison.activity4_results.results_io` |
| Regenerar el informe de resultados (necesita `pdflatex`) | `python -m section3_deliverables.build_results_report` |

## Carpetas

```
main.py                         ventana principal
theme.py                        colores, fuentes y tiempos de la interfaz
requirements.txt                dependencias
brief/                          enunciado
section1_comparison/            punto 1: análisis y comparación
  activity1_formal_analysis/    análisis formal (PDF del examen y anexo_analisis_formal.pdf, con su fuente .tex)
  activity2_implementation/     algoritmos y sus pruebas
  activity3_experiment/         datos de entrada, medición y conteos
  activity4_results/            pestaña de comparación, gráficas y archivos de resultados
section2_animation/             punto 2: pestaña de animación, reproducción y pruebas
section3_deliverables/          punto 3: entregables
  resultados_experimentales.pdf metodología, resultados e interpretación
  bitacora_ia.md                registro del desarrollo con agentes de IA
  build_results_report.py       genera el PDF de resultados
  charts/                       las 7 gráficas
  data/                         todos los datos medidos y el equipo usado
```
