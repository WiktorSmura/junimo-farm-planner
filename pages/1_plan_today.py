from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State, callback, dash_table, dcc, html, no_update, register_page

from src.figures import CHART_COLORS, axis_style, base_layout

register_page(__name__, path="/", name="Plan Today", order=1)

METRIC_OPTIONS = [
    {"label": "Total Profit", "value": "profit_total"},
    {"label": "Profit per Day", "value": "profit_per_day"},
    {"label": "ROI", "value": "roi"},
    {"label": "First Harvest Speed", "value": "first_harvest_day"},
]

METRIC_LABELS = {option["value"]: option["label"] for option in METRIC_OPTIONS}

TABLE_COLUMNS = [
    {"name": "Crop", "id": "crop_name"},
    {"name": "Season", "id": "season"},
    {"name": "Seed Price", "id": "seed_price"},
    {"name": "Sell Price", "id": "sell_price_effective"},
    {"name": "Growth Days", "id": "growth_days"},
    {"name": "Harvests", "id": "harvest_count"},
    {"name": "Seed Cost", "id": "seed_cost"},
    {"name": "Total Profit", "id": "profit_total"},
    {"name": "Profit/Day", "id": "profit_per_day"},
    {"name": "ROI", "id": "roi"},
    {"name": "Affordable", "id": "affordable"},
    {"name": "Will Mature", "id": "can_mature"},
]

layout = html.Div(
    className="page-card",
    children=[
        html.Div(
            className="page-head",
            children=[
                html.P("Main decision page", className="badge"),
                html.H2("Plan Today"),
                html.P("Decide what to plant now using ranked recommendations and tradeoff details."),
            ],
        ),
        html.Section(
            className="plan-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Top Recommendations"),
                        html.P("Best immediate options under current constraints."),
                    ],
                ),
                html.Div(id="plan-recommendation-cards", className="plan-cards"),
            ],
        ),
        html.Section(
            className="plan-section leaderboard-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Leaderboard"),
                        html.P("Compare the strongest crops by your selected metric."),
                    ],
                ),
                html.Div(
                    className="plan-leaderboard-controls",
                    children=[
                        html.Div(
                            className="control-field",
                            children=[
                                html.Label("Leaderboard metric", className="control-label"),
                                dcc.Dropdown(
                                    id="plan-metric-control",
                                    options=METRIC_OPTIONS,
                                    value="profit_per_day",
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-field",
                            children=[
                                html.Label("Top N", className="control-label"),
                                dcc.Slider(
                                    id="plan-topn-control",
                                    min=3,
                                    max=20,
                                    step=1,
                                    value=8,
                                    marks={3: "3", 8: "8", 12: "12", 16: "16", 20: "20"},
                                ),
                            ],
                        ),
                    ],
                ),
                dcc.Graph(
                    id="plan-leaderboard-graph",
                    className="leaderboard-graph",
                    style={"height": "430px", "minHeight": "430px"},
                    config={"displayModeBar": False, "responsive": True},
                ),
            ],
        ),
        html.Div(
            className="plan-details-grid",
            children=[
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Selected Crop Diagnostics"),
                                html.P("Economics and timing for the selected crop."),
                            ],
                        ),
                        html.Div(id="plan-selected-detail", className="detail-card"),
                        html.Div(
                            className="detail-card harvest-preview-card",
                            children=[
                                html.H3("Harvest Preview"),
                                html.Div(
                                    id="plan-harvest-preview",
                                    className="harvest-preview-body",
                                ),
                            ],
                        ),
                    ],
                ),
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Budget and Warnings"),
                                html.P("Seed spend against budget and rule flags."),
                            ],
                        ),
                        html.Div(
                            className="plan-grid",
                            children=[
                                dcc.Graph(
                                    id="plan-budget-gauge",
                                    className="budget-graph",
                                    config={"displayModeBar": False, "responsive": True},
                                ),
                                html.Div(id="plan-warning-panel", className="detail-card"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Section(
            className="plan-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Crop Table"),
                        html.P("Filter, sort, and select a crop to drive details below."),
                    ],
                ),
                dash_table.DataTable(
                    id="plan-crop-table",
                    columns=TABLE_COLUMNS,
                    data=[],
                    row_selectable="single",
                    selected_rows=[],
                    sort_action="native",
                    filter_action="native",
                    page_size=10,
                    style_as_list_view=True,
                    style_table={"overflowX": "auto", "width": "100%", "maxWidth": "100%"},
                    style_cell={
                        "fontFamily": "Inter, Segoe UI, sans-serif",
                        "fontSize": 13,
                        "maxWidth": 170,
                        "minWidth": 90,
                        "overflow": "hidden",
                        "padding": "8px",
                        "textOverflow": "ellipsis",
                    },
                    style_header={"fontFamily": "Inter, Segoe UI, sans-serif", "fontWeight": 700},
                    css=[{"selector": ".dash-spreadsheet", "rule": "max-width: 100%;"}],
                ),
            ],
        ),
    ],
)


@callback(
    Output("plan-crop-table", "data"),
    Output("plan-crop-table", "selected_rows"),
    Input("filtered-crops-store", "data"),
    Input("selected-crop-store", "data"),
)
def populate_plan_table(rows: list[dict] | None, selected_crop: dict | None):
    rows = rows or []
    if not rows:
        return [], []

    table_rows = [_to_table_row(row) for row in rows]

    selected_id = selected_crop["crop_id"] if selected_crop else None
    selected_index = 0
    if selected_id:
        for index, row in enumerate(table_rows):
            if row["crop_id"] == selected_id:
                selected_index = index
                break
    return table_rows, [selected_index]


@callback(
    Output("plan-recommendation-cards", "children"),
    Output("plan-leaderboard-graph", "figure"),
    Output("plan-leaderboard-graph", "style"),
    Output("plan-selected-detail", "children"),
    Output("plan-harvest-preview", "children"),
    Output("plan-budget-gauge", "figure"),
    Output("plan-warning-panel", "children"),
    Input("plan-crop-table", "derived_virtual_data"),
    Input("plan-crop-table", "derived_virtual_selected_rows"),
    Input("plan-metric-control", "value"),
    Input("plan-topn-control", "value"),
    State("budget-control", "value"),
)
def update_plan_today_views(
    visible_rows: list[dict] | None,
    selected_rows: list[int] | None,
    metric: str,
    top_n: int,
    budget: float | None,
):
    rows = visible_rows or []
    if not rows:
        empty_chart = go.Figure()
        empty_chart.update_layout(template=None, height=320, margin={"l": 20, "r": 20, "t": 20, "b": 20})
        empty_chart.add_annotation(
            text="No matching crops for current filters",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
        return (
            [html.Div("No recommendations to show.", className="detail-card")],
            empty_chart,
            _leaderboard_style(320),
            [html.H3("No crop selected"), html.P("Adjust filters to see recommendations.")],
            _empty_harvest_preview(),
            _empty_budget_figure(),
            [html.H3("Warnings"), html.P("No warnings because no crop is selected.")],
        )

    selected_index = selected_rows[0] if selected_rows else 0
    selected_index = max(0, min(selected_index, len(rows) - 1))
    selected = rows[selected_index]

    cards = _build_recommendation_cards(rows[:3])
    leaderboard = _build_leaderboard(rows, selected["crop_id"], metric, top_n)
    leaderboard_style = _leaderboard_style(int(leaderboard.layout.height or 430))
    detail = _build_selected_detail(selected)
    harvest_preview = _build_harvest_preview(selected)
    budget_chart = _build_budget_chart(selected, budget)
    warning_panel = _build_warning_panel(selected)

    return cards, leaderboard, leaderboard_style, detail, harvest_preview, budget_chart, warning_panel


@callback(
    Output("selected-crop-store", "data", allow_duplicate=True),
    Input("plan-crop-table", "derived_virtual_data"),
    Input("plan-crop-table", "derived_virtual_selected_rows"),
    prevent_initial_call=True,
)
def sync_selected_crop_store(visible_rows: list[dict] | None, selected_rows: list[int] | None):
    rows = visible_rows or []
    if not rows:
        return None

    selected_index = selected_rows[0] if selected_rows else 0
    selected_index = max(0, min(selected_index, len(rows) - 1))
    return rows[selected_index]


@callback(
    Output("selected-crop-store", "data", allow_duplicate=True),
    Input("plan-leaderboard-graph", "clickData"),
    State("plan-crop-table", "derived_virtual_data"),
    prevent_initial_call=True,
)
def select_crop_from_leaderboard(click_data: dict | None, visible_rows: list[dict] | None):
    crop_id = _clicked_crop_id(click_data)
    if not crop_id:
        return no_update

    for row in visible_rows or []:
        if row.get("crop_id") == crop_id:
            return row
    return no_update


def _build_recommendation_cards(top_rows: list[dict]) -> list[html.Div]:
    labels = ["Best Profit", "Runner-up", "Alternative"]
    cards = []
    for index, row in enumerate(top_rows):
        cards.append(
            html.Div(
                className="detail-card recommendation-card",
                children=[
                    html.P(labels[index], className="badge"),
                    html.H3(row["crop_name"]),
                    html.P(f"{row['profit_total']:.0f}g expected total profit"),
                    html.P(f"{row['profit_per_day']:.1f}g/day"),
                    html.P(f"{row['harvest_count']} harvests, {row['seed_cost']:.0f}g seed cost"),
                    _warning_badges(row),
                ],
            )
        )
    return cards


def _warning_badges(row: dict) -> html.Div:
    flags = row.get("warning_flags") or []
    if isinstance(flags, str):
        flags = [flag for flag in flags.split("|") if flag]
    badges = list(flags)
    if row.get("affordable") is True:
        badges.append("Affordable")
    if row.get("is_regrowable"):
        badges.append("Regrows")
    if not badges:
        badges = ["Ready"]
    return html.Div(
        className="warning-flags recommendation-badges",
        children=[html.Span(badge, className="warning-flag") for badge in badges[:4]],
    )


def _build_leaderboard(rows: list[dict], selected_crop_id: str, metric: str, top_n: int) -> go.Figure:
    ranked = list(rows)
    if metric == "first_harvest_day":
        ranked.sort(key=lambda row: row["first_harvest_day"])
    else:
        ranked.sort(key=lambda row: row[metric], reverse=True)
    ranked = ranked[: max(3, int(top_n))]

    metric_label = METRIC_LABELS.get(metric, metric.replace("_", " ").title())
    colors = [CHART_COLORS["gold"] if row["crop_id"] == selected_crop_id else CHART_COLORS["green"] for row in ranked]
    opacities = [1.0 if row["crop_id"] == selected_crop_id else 0.58 for row in ranked]
    values = [row[metric] for row in ranked]
    names = [row["crop_name"] for row in ranked]
    text_values = [_format_metric_value(value, metric) for value in values]
    custom_data = [
        [
            row["crop_id"],
            row["crop_name"],
            row["profit_total"],
            row["profit_per_day"],
            row["harvest_count"],
            row["seed_cost"],
        ]
        for row in ranked
    ]
    max_value = max(values) if values else 1
    chart_height = min(560, max(320, 120 + len(ranked) * 38))

    figure = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            customdata=custom_data,
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                f"{metric_label}: %{{text}}<br>"
                "Total profit: %{customdata[2]:,.0f}g<br>"
                "Profit/day: %{customdata[3]:,.1f}g<br>"
                "Harvests: %{customdata[4]}<br>"
                "Seed cost: %{customdata[5]:,.0f}g<extra>Click to select</extra>"
            ),
            marker={
                "color": colors,
                "line": {"color": CHART_COLORS["cream"], "width": 1},
                "opacity": opacities,
            },
            text=text_values,
            textposition="auto",
            textfont={"color": CHART_COLORS["ink"], "size": 12},
            cliponaxis=True,
        )
    )
    figure.update_layout(
        **base_layout(height=chart_height, margin={"l": 132, "r": 92, "t": 18, "b": 54}),
        bargap=0.36,
        dragmode=False,
        autosize=True,
        showlegend=False,
        transition={"duration": 180},
        yaxis={
            "autorange": "reversed",
            "automargin": True,
            "fixedrange": True,
            "showgrid": False,
            "tickfont": {"color": CHART_COLORS["ink"], "size": 12},
        },
        xaxis={
            **axis_style(metric_label),
            "range": [0, max_value * 1.16 if max_value > 0 else 1],
        },
    )
    return figure


def _leaderboard_style(height: int) -> dict[str, str]:
    height = max(320, int(height))
    return {"height": f"{height}px", "minHeight": f"{height}px"}


def _build_selected_detail(row: dict) -> list[object]:
    return [
        html.H3(row["crop_name"]),
        html.Div(
            className="metric-grid",
            children=[
                _metric_tile("Season", row["season"]),
                _metric_tile("First harvest", f"Day {row['first_harvest_day']}"),
                _metric_tile("Harvests", f"{row['harvest_count']}"),
                _metric_tile("Revenue", f"{row['revenue']:,.0f}g"),
                _metric_tile("Seed cost", f"{row['seed_cost']:,.0f}g"),
                _metric_tile("Total profit", f"{row['profit_total']:,.0f}g"),
                _metric_tile("ROI", f"{row['roi']:.2f}"),
            ],
        ),
        html.P(row.get("rule_note") or "No special crop restriction."),
    ]


def _build_harvest_preview(row: dict) -> list[object]:
    first_harvest = int(row.get("first_harvest_day", 0) or 0)
    window_days = int(row.get("window_days", 28) or 28)
    harvest_count = int(row.get("harvest_count", 0) or 0)

    if harvest_count < 1 or first_harvest < 1:
        return _empty_harvest_preview("No harvest before the end of the selected planting window.")

    regrowth_days = int(row.get("regrowth_days", 0) or 0)
    harvest_days = [first_harvest]
    if regrowth_days > 0:
        for _ in range(1, harvest_count):
            harvest_days.append(harvest_days[-1] + regrowth_days)
    else:
        growth_days = int(row.get("growth_days", 1) or 1)
        for _ in range(1, harvest_count):
            harvest_days.append(harvest_days[-1] + growth_days)

    harvest_days = [day for day in harvest_days if day <= window_days]
    if not harvest_days:
        return _empty_harvest_preview("No harvest before the end of the selected planting window.")

    visible_days = harvest_days[:10]
    hidden_count = max(0, len(harvest_days) - len(visible_days))
    interval = f"Every {regrowth_days} days after first harvest" if regrowth_days > 0 else "Replanted after each harvest"

    day_nodes = [html.Span(f"Day {day}", className="harvest-day-pill") for day in visible_days]
    if hidden_count:
        day_nodes.append(html.Span(f"+{hidden_count} more", className="harvest-day-pill harvest-day-more"))

    return [
        html.Div(
            className="harvest-preview-summary",
            children=[
                _harvest_stat("First harvest", f"Day {harvest_days[0]}"),
                _harvest_stat("Last harvest", f"Day {harvest_days[-1]}"),
                _harvest_stat("Total harvests", str(len(harvest_days))),
            ],
        ),
        html.P(interval, className="harvest-preview-note"),
        html.Div(className="harvest-day-row", children=day_nodes),
    ]


def _harvest_stat(label: str, value: str) -> html.Div:
    return html.Div(
        className="harvest-stat",
        children=[
            html.Span(label, className="metric-label"),
            html.Strong(value, className="metric-value"),
        ],
    )


def _empty_harvest_preview(message: str = "Select a crop to preview harvest days.") -> list[object]:
    return [html.P(message, className="harvest-preview-note")]


def _build_budget_chart(row: dict, budget: float | None) -> go.Figure:
    usable_budget = float(budget) if budget not in (None, "") else row["seed_cost"]
    max_budget = max(1.0, usable_budget)
    seed_cost = float(row["seed_cost"])
    remaining_budget = max(0.0, max_budget - seed_cost)
    overspend = max(0.0, seed_cost - max_budget)

    figure = go.Figure()
    seed_bar = min(seed_cost, max_budget)
    figure.add_bar(
        name="Seed cost",
        y=["Budget"],
        x=[seed_bar],
        orientation="h",
        marker_color=CHART_COLORS["green"],
        hovertemplate="Seed cost: %{x:,.0f}g<extra></extra>",
    )
    figure.add_bar(
        name="Remaining",
        y=["Budget"],
        x=[remaining_budget],
        orientation="h",
        marker_color=CHART_COLORS["tan"],
        hovertemplate="Remaining: %{x:,.0f}g<extra></extra>",
    )
    if overspend > 0:
        figure.add_bar(
            name="Over budget",
            y=["Budget"],
            x=[overspend],
            orientation="h",
            marker_color=CHART_COLORS["red"],
            hovertemplate="Over budget: %{x:,.0f}g<extra></extra>",
        )

    figure.update_layout(
        **base_layout(height=190, margin={"l": 8, "r": 8, "t": 48, "b": 42}),
        barmode="stack",
        autosize=True,
        title={"text": f"Budget Meter ({seed_cost:,.0f}g of {max_budget:,.0f}g used)", "x": 0, "xanchor": "left"},
        xaxis={
            **axis_style("Gold", ticksuffix="g"),
            "range": [0, max(seed_cost, max_budget) * 1.08],
        },
        yaxis={"fixedrange": True, "showticklabels": False},
        showlegend=False,
    )
    figure.add_vline(
        x=max_budget,
        line_color=CHART_COLORS["ink"],
        line_dash="dot",
        line_width=1,
        opacity=0.55,
    )
    return figure


def _empty_budget_figure() -> go.Figure:
    figure = go.Figure()
    figure.update_layout(height=170, margin={"l": 20, "r": 20, "t": 20, "b": 20})
    return figure


def _empty_figure(message: str, height: int) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        height=height,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    figure.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    return figure


def _build_warning_panel(row: dict) -> list[object]:
    raw_warning_flags = row.get("warning_flags")
    if isinstance(raw_warning_flags, list):
        warnings = list(raw_warning_flags)
    elif isinstance(raw_warning_flags, str):
        warnings = [item for item in raw_warning_flags.split("|") if item]
    else:
        warnings = []
    if not warnings:
        warnings = ["No critical warnings for the current settings."]

    detail_messages = []
    for warning in warnings:
        if warning == "Too Late":
            detail_messages.append("This crop is unlikely to mature before the end of the available season window.")
        elif warning == "Over Budget":
            detail_messages.append("Seed cost exceeds your current budget limit.")
        elif warning == "Trellis":
            detail_messages.append("Trellis crops can block movement and may affect tile layout.")
        elif warning == "Quest-only":
            detail_messages.append("This crop is only available during specific quest conditions.")
        else:
            detail_messages.append(warning)

    return [
        html.H3("Warnings"),
        html.Ul([html.Li(message) for message in detail_messages], className="detail-list"),
    ]


def _metric_tile(label: str, value: str) -> html.Div:
    return html.Div(
        className="metric-tile",
        children=[
            html.Span(label, className="metric-label"),
            html.Strong(value, className="metric-value"),
        ],
    )


def _format_metric_value(value: float | int, metric: str) -> str:
    if metric in {"profit_total", "profit_per_day"}:
        return f"{float(value):,.1f}g" if metric == "profit_per_day" else f"{float(value):,.0f}g"
    if metric == "roi":
        return f"{float(value):.2f}x"
    if metric == "first_harvest_day":
        return f"Day {int(value)}"
    if isinstance(value, float):
        return f"{value:,.1f}"
    return str(value)


def _clicked_crop_id(click_data: dict | None) -> str | None:
    points = (click_data or {}).get("points") or []
    if not points:
        return None

    custom_data = points[0].get("customdata")
    if isinstance(custom_data, list) and custom_data:
        return str(custom_data[0])
    if isinstance(custom_data, str):
        return custom_data
    return None


def _to_table_row(row: dict) -> dict:
    table_row = dict(row)
    warning_flags = row.get("warning_flags") or []
    if isinstance(warning_flags, list):
        table_row["warning_flags"] = "|".join(str(flag) for flag in warning_flags)
    elif warning_flags is None:
        table_row["warning_flags"] = ""
    else:
        table_row["warning_flags"] = str(warning_flags)
    return table_row
