"""Shared paths, constants and chart style for the capstone."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXTERNAL = ROOT / "data" / "external"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"
TABLES = ROOT / "reports" / "tables"
DASHBOARD = ROOT / "dashboard"

for p in (RAW, PROCESSED, FIGURES, TABLES, DASHBOARD):
    p.mkdir(parents=True, exist_ok=True)

SEED = 2026
START_DATE = "2024-10-01"
END_DATE = "2026-09-30"          # 24 full months of transactions

# Churn: a customer is "churned" if they make no purchase in the 90 days after a cutoff.
CHURN_WINDOW_DAYS = 90

# Validated categorical palette (light mode) - fixed order, never cycled.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
           "#e87ba4", "#008300", "#6250d6", "#e34948"]
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"


def set_style():
    """Apply a consistent, recessive-grid matplotlib style."""
    import matplotlib as mpl
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": TEXT_2,
        "axes.titlecolor": TEXT, "axes.titlesize": 13, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": TEXT_2, "ytick.color": TEXT_2, "font.size": 10.5,
        "lines.linewidth": 2, "axes.prop_cycle": mpl.cycler(color=PALETTE),
        "legend.frameon": False, "figure.dpi": 110, "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })


def kes(x, pos=None):
    """Axis formatter for shilling amounts with K/M suffix (axis titles carry the KES unit)."""
    if abs(x) >= 1e6:
        v = x / 1e6
        return f"{v:.0f}M" if float(v).is_integer() else f"{v:.1f}M"
    if abs(x) >= 1e3:
        return f"{x/1e3:.0f}K"
    return f"{x:.0f}"
