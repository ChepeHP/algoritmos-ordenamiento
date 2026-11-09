"""Bubble Sort and Quicksort: experimental comparison and Quicksort animation. Run: python main.py"""

import tkinter as tk
from tkinter import ttk

import theme
from section1_comparison.activity4_results.comparison_tab import ComparisonTab
from section2_animation.animation_tab import AnimationTab


def main():
    root = tk.Tk()
    root.title("Análisis de algoritmos de ordenamiento")
    root.geometry("1320x860")
    root.minsize(1120, 780)
    fonts = theme.apply_style(root)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    notebook.add(ComparisonTab(notebook, fonts), text="Comparar algoritmos")
    notebook.add(AnimationTab(notebook, fonts), text="Animar Quicksort")
    root.mainloop()


if __name__ == "__main__":
    main()
