"""Design tokens for the whole app. Widgets and charts take every colour, font and duration from here."""

import tkinter.font as tkfont
from tkinter import ttk

# Chrome, from the generated OKLCH ramp at hue 250.
PAGE = "#f3f8fd"
SURFACE = "#f9fdff"
RAISED = "#e4e9ee"
BORDER = "#d1d5da"
BORDER_STRONG = "#abb0b4"
# Edge of anything that takes input: at least 3:1 against the surface.
CONTROL_BORDER = "#868c92"
TEXT_SECONDARY = "#51565a"
TEXT_MUTED = "#6b7278"
ERROR = "#ba4878"

# Prussian blue: the drawing surface, also the ink and the primary action.
INK = "#13324f"
INK_HOVER = "#395871"
ON_INK = "#fdfdfd"

# Plot states, chosen against the Prussian blue. Each also has a non-colour mark.
PLOT_BAR = "#adcae5"
PLOT_BAR_DIM = "#5587b0"
PLOT_GRID = "#324e69"
PLOT_REGION = "#1b4063"
PLOT_TEXT = "#d7e3ee"
PLOT_TEXT_MUTED = "#92b6d3"
STATE_COMPARE = "#e0d473"
STATE_PIVOT = "#e1779f"
STATE_PIVOT_TEXT = "#f093b5"
STATE_SORTED = "#7deabb"
STATE_SWAP = "#fdfdfd"

# Chart series, validated with the dataviz palette script (CVD delta E 23.2).
BUBBLE = "#1f5fa8"
QUICK = "#d2601a"
CHART_SURFACE = "#fdfdfd"
CHART_GRID = "#e4e9ee"

SPACE_XS = 4
SPACE_S = 8
SPACE_M = 12
SPACE_L = 20
# Wrap width of the side panels' messages, so a long message cannot widen the panel.
PANEL_TEXT_WIDTH = 360

STEP_MS = 650
FRAME_MS = 16
SWAP_SHARE = 0.85
POLL_MS = 150

# Tk has no way to load a font file, so these are searched among the installed fonts.
UI_FAMILIES = ["Hanken Grotesk", "Segoe UI", "Helvetica Neue", "Cantarell", "DejaVu Sans", "Liberation Sans"]
MONO_FAMILIES = ["Hack", "Consolas", "Menlo", "DejaVu Sans Mono", "Liberation Mono", "Courier New"]


def cubic_bezier(x1, y1, x2, y2):
    """Return an easing function t -> progress for a CSS-style cubic Bezier curve."""

    def axis(t, a, b):
        return 3 * (1 - t) ** 2 * t * a + 3 * (1 - t) * t**2 * b + t**3

    def ease(x):
        low, high = 0.0, 1.0
        for _ in range(24):
            mid = (low + high) / 2
            if axis(mid, x1, x2) < x:
                low = mid
            else:
                high = mid
        return axis((low + high) / 2, y1, y2)

    return ease


EASE_MOVE = cubic_bezier(0.77, 0, 0.175, 1)


def _first_installed(root, families):
    installed = set(tkfont.families(root))
    for family in families:
        if family in installed:
            return family
    return families[-1]


class Fonts:
    """Named font tuples, resolved once the Tk root exists."""

    def __init__(self, root):
        ui = _first_installed(root, UI_FAMILIES)
        mono = _first_installed(root, MONO_FAMILIES)
        self.body = (ui, 11)
        self.small = (ui, 10)
        self.strong = (ui, 11, "bold")
        self.heading = (ui, 12, "bold")
        self.narration = (ui, 15)
        self.tab = (ui, 12)
        self.code = (mono, 10)
        self.value = (mono, 11)
        self.plot = (mono, 9)
        self.plot_small = (mono, 8)
        self.plot_ui = (ui, 10)


def apply_style(root):
    fonts = Fonts(root)
    root.configure(bg=PAGE)
    root.option_add("*TCombobox*Listbox.font", fonts.body)
    root.option_add("*TCombobox*Listbox.background", SURFACE)
    root.option_add("*TCombobox*Listbox.foreground", INK)
    root.option_add("*TCombobox*Listbox.selectBackground", INK)
    root.option_add("*TCombobox*Listbox.selectForeground", ON_INK)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=PAGE, foreground=INK, font=fonts.body, bordercolor=BORDER,
                    lightcolor=PAGE, darkcolor=PAGE, troughcolor=RAISED, focuscolor=INK)
    style.configure("TFrame", background=PAGE)
    style.configure("Panel.TFrame", background=SURFACE)
    style.configure("TLabel", background=PAGE, foreground=INK)
    style.configure("Panel.TLabel", background=SURFACE, foreground=INK)
    style.configure("Heading.TLabel", background=SURFACE, foreground=INK, font=fonts.heading)
    style.configure("Hint.TLabel", background=SURFACE, foreground=TEXT_MUTED, font=fonts.small)
    style.configure("Error.TLabel", background=SURFACE, foreground=ERROR, font=fonts.small)
    style.configure("Value.TLabel", background=SURFACE, foreground=INK, font=fonts.value)
    style.configure("Narration.TLabel", background=PAGE, foreground=INK, font=fonts.narration)
    style.configure("Step.TLabel", background=PAGE, foreground=TEXT_SECONDARY, font=fonts.value)
    style.configure("Legend.TLabel", background=PAGE, foreground=TEXT_SECONDARY, font=fonts.small)

    style.configure("TNotebook", background=PAGE, borderwidth=0, tabmargins=(SPACE_L, SPACE_S, 0, 0))
    style.configure("TNotebook.Tab", background=PAGE, foreground=TEXT_SECONDARY, font=fonts.tab,
                    padding=(SPACE_L, SPACE_S), borderwidth=0)
    # Clam shrinks the selected tab unless its padding is mapped too.
    style.map("TNotebook.Tab", background=[("selected", SURFACE), ("active", RAISED)],
              foreground=[("selected", INK)], padding=[("selected", (SPACE_L, SPACE_S))])

    style.configure("Inner.TNotebook", background=SURFACE, borderwidth=0, tabmargins=(0, SPACE_XS, 0, 0))
    style.configure("Inner.TNotebook.Tab", background=SURFACE, foreground=TEXT_SECONDARY, font=fonts.small,
                    padding=(SPACE_S, SPACE_XS), borderwidth=0)
    style.map("Inner.TNotebook.Tab", background=[("selected", PAGE), ("active", RAISED)],
              foreground=[("selected", INK)], padding=[("selected", (SPACE_S, SPACE_XS))])

    style.configure("TButton", background=SURFACE, foreground=INK, bordercolor=BORDER_STRONG,
                    lightcolor=SURFACE, darkcolor=SURFACE, padding=(SPACE_M, SPACE_XS), relief="raised",
                    borderwidth=1, width=-6)
    style.map("TButton", background=[("disabled", SURFACE), ("active", RAISED)],
              lightcolor=[("active", RAISED)], darkcolor=[("active", RAISED)],
              foreground=[("disabled", BORDER_STRONG)], bordercolor=[("disabled", BORDER)])
    style.configure("Primary.TButton", background=INK, foreground=ON_INK, bordercolor=INK,
                    lightcolor=INK, darkcolor=INK, font=fonts.strong, focuscolor=ON_INK)
    style.map("Primary.TButton", background=[("disabled", RAISED), ("active", INK_HOVER)],
              lightcolor=[("disabled", RAISED), ("active", INK_HOVER)],
              darkcolor=[("disabled", RAISED), ("active", INK_HOVER)],
              foreground=[("disabled", TEXT_MUTED)], bordercolor=[("disabled", BORDER)])

    style.configure("TEntry", fieldbackground=SURFACE, foreground=INK, bordercolor=CONTROL_BORDER,
                    insertcolor=INK, padding=SPACE_XS)
    style.map("TEntry", bordercolor=[("focus", INK)], lightcolor=[("focus", INK)])
    for name in ("TCombobox", "TSpinbox"):
        style.configure(name, fieldbackground=SURFACE, background=SURFACE, foreground=INK,
                        bordercolor=CONTROL_BORDER, arrowcolor=INK, padding=SPACE_XS, insertcolor=INK)
        style.map(name, bordercolor=[("focus", INK)], lightcolor=[("focus", INK)],
                  fieldbackground=[("readonly", SURFACE)], foreground=[("readonly", INK)],
                  selectbackground=[("readonly", SURFACE)], selectforeground=[("readonly", INK)])
    style.configure("TCheckbutton", background=SURFACE, foreground=INK, indicatorcolor=SURFACE,
                    indicatorbackground=SURFACE, indicatorsize=14, padding=0)
    style.map("TCheckbutton", background=[("active", SURFACE)], indicatorcolor=[("selected", INK)])
    style.configure("Horizontal.TScale", background=INK, troughcolor=BORDER, bordercolor=BORDER,
                    lightcolor=INK, darkcolor=INK)
    style.configure("Horizontal.TProgressbar", background=INK, troughcolor=RAISED, bordercolor=RAISED,
                    lightcolor=INK, darkcolor=INK)
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=INK,
                    font=fonts.code, rowheight=tkfont.Font(root=root, font=fonts.code).metrics("linespace") + SPACE_XS,
                    bordercolor=BORDER)
    style.map("Treeview", background=[("selected", INK)], foreground=[("selected", ON_INK)])
    style.configure("Treeview.Heading", background=RAISED, foreground=INK, font=fonts.small,
                    relief="flat", padding=(SPACE_XS, SPACE_XS))
    style.map("Treeview.Heading", background=[("active", BORDER)])
    return fonts
