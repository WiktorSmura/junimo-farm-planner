CHART_COLORS = {
    "ink": "#2d2418",
    "text": "#403523",
    "muted": "#756852",
    "grid": "#d8c28a",
    "paper": "rgba(0,0,0,0)",
    "plot": "rgba(0,0,0,0)",
    "green": "#4f8a3d",
    "green_dark": "#346b32",
    "gold": "#c4872f",
    "tan": "#ead9aa",
    "brown": "#8b6a32",
    "red": "#b84c3f",
    "cream": "#fff6dc",
}

CHART_PALETTE = [
    CHART_COLORS["green"],
    CHART_COLORS["gold"],
    CHART_COLORS["brown"],
    "#6e8f3d",
    CHART_COLORS["red"],
    "#2f6f44",
    "#9f641d",
    "#5f7f93",
]


def hover_label_style() -> dict:
    return {
        "bgcolor": CHART_COLORS["ink"],
        "bordercolor": CHART_COLORS["ink"],
        "font": {"color": "#ffffff", "family": "Inter, Segoe UI, sans-serif", "size": 12},
    }


def axis_style(title: str | None = None, ticksuffix: str | None = None) -> dict:
    axis = {
        "automargin": True,
        "fixedrange": True,
        "gridcolor": CHART_COLORS["grid"],
        "linecolor": CHART_COLORS["grid"],
        "showline": True,
        "tickfont": {"color": CHART_COLORS["muted"], "size": 11},
        "zeroline": False,
    }
    if title:
        axis["title"] = {"text": title, "standoff": 12}
    if ticksuffix:
        axis["ticksuffix"] = ticksuffix
    return axis


def base_layout(height: int, margin: dict | None = None) -> dict:
    return {
        "height": height,
        "margin": margin or {"l": 48, "r": 24, "t": 24, "b": 48},
        "font": {"color": CHART_COLORS["text"], "family": "Inter, Segoe UI, sans-serif", "size": 12},
        "hoverlabel": hover_label_style(),
        "paper_bgcolor": CHART_COLORS["paper"],
        "plot_bgcolor": CHART_COLORS["plot"],
    }


def money_label(value: float, decimals: int = 0) -> str:
    return f"{float(value):,.{decimals}f}g"
