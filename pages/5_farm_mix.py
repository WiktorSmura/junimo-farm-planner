from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State, callback, dash_table, dcc, html, register_page

from src.farm_mix import allocate_mix, rank_mix_candidates, summarize_mix

register_page(__name__, path="/farm-mix", name="Farm Mix", order=5)

STRATEGY_OPTIONS = [
    {"label": "Max profit", "value": "max_profit"},
    {"label": "Quick cash", "value": "quick_cash"},
    {"label": "Low effort", "value": "low_effort"},
    {"label": "Balanced", "value": "balanced"},
]

TABLE_COLUMNS = [
    {"name": "Crop", "id": "crop_name"},
    {"name": "Tiles", "id": "tiles"},
    {"name": "Seed Cost", "id": "seed_cost"},
    {"name": "Harvest Count", "id": "harvest_count"},
    {"name": "Revenue", "id": "revenue"},
    {"name": "Profit", "id": "profit"},
    {"name": "Profit/Day", "id": "profit_per_day"},
    {"name": "ROI", "id": "roi"},
]


def _control_field(title: str, body: object) -> html.Div:
    return html.Div(
        className="control-field",
        children=[
            html.Label(title, className="control-label"),
            body,
        ],
    )


layout = html.Div(
    className="page-card mix-page",
    children=[
        html.Div(
            className="page-head",
            children=[
                html.P("Allocation workspace", className="badge"),
                html.H2("Farm Mix"),
                html.P("Build a practical planting mix that fits both budget and tile constraints."),
            ],
        ),
        html.Section(
            className="plan-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Mix Controls"),
                        html.P("Choose strategy and constraints for allocation."),
                    ],
                ),
                html.Div(
                    className="explorer-control-grid",
                    children=[
                        _control_field(
                            "Strategy",
                            dcc.Dropdown(
                                id="mix-strategy",
                                options=STRATEGY_OPTIONS,
                                value="balanced",
                                clearable=False,
                            ),
                        ),
                        _control_field(
                            "Top N",
                            dcc.Slider(
                                id="mix-top-n",
                                min=3,
                                max=20,
                                step=1,
                                value=8,
                                marks={3: "3", 8: "8", 12: "12", 16: "16", 20: "20"},
                            ),
                        ),
                        _control_field(
                            "Crop cap (%)",
                            dcc.Slider(
                                id="mix-cap-percent",
                                min=20,
                                max=100,
                                step=5,
                                value=60,
                                marks={20: "20", 40: "40", 60: "60", 80: "80", 100: "100"},
                            ),
                        ),
                    ],
                ),
                html.Div(
                    className="control-field",
                    style={"marginTop": "12px"},
                    children=[
                        html.Label("Allowed crops", className="control-label"),
                        dcc.Dropdown(id="mix-allowed-crops", multi=True, options=[], value=[]),
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
                        html.H3("Mix Summary"),
                        html.P("Core economics of the generated planting mix."),
                    ],
                ),
                html.Div(id="mix-kpi-cards", className="plan-cards"),
            ],
        ),
        html.Div(
            className="processing-chart-grid",
            children=[
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[html.H3("Planting Treemap"), html.P("Each rectangle represents crop tile allocation.")],
                        ),
                        dcc.Graph(
                            id="mix-treemap",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "460px"},
                        ),
                    ],
                ),
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Budget Allocation"),
                                html.P("Seed spend by crop against the available budget."),
                            ],
                        ),
                        dcc.Graph(
                            id="mix-budget-chart",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "380px"},
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
                        html.H3("Planting Plan"),
                        html.P("Concrete allocation rows used by both charts."),
                    ],
                ),
                dash_table.DataTable(
                    id="mix-plan-table",
                    columns=TABLE_COLUMNS,
                    data=[],
                    sort_action="native",
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
                ),
            ],
        ),
    ],
)


@callback(
    Output("mix-allowed-crops", "options"),
    Output("mix-allowed-crops", "value"),
    Input("filtered-crops-store", "data"),
    State("mix-allowed-crops", "value"),
)
def sync_mix_allowed_crops(rows: list[dict] | None, selected: list[str] | None):
    rows = rows or []
    eligible = [row for row in rows if row.get("profit_supported", True) and row.get("can_mature", False)]
    options = [{"label": row["crop_name"], "value": row["crop_id"]} for row in eligible]
    valid = {option["value"] for option in options}

    current = [crop_id for crop_id in (selected or []) if crop_id in valid]
    if not current:
        current = [option["value"] for option in options]
    return options, current


@callback(
    Output("mix-kpi-cards", "children"),
    Output("mix-treemap", "figure"),
    Output("mix-budget-chart", "figure"),
    Output("mix-plan-table", "data"),
    Input("filtered-crops-store", "data"),
    Input("mix-strategy", "value"),
    Input("mix-top-n", "value"),
    Input("mix-cap-percent", "value"),
    Input("mix-allowed-crops", "value"),
    State("tiles-control", "value"),
    State("budget-control", "value"),
)
def update_mix_page(
    rows: list[dict] | None,
    strategy: str,
    top_n: int,
    cap_percent: int,
    allowed_crops: list[str] | None,
    tiles: int | None,
    budget: float | None,
):
    rows = rows or []
    allowed = set(allowed_crops or [])
    scoped_rows = [row for row in rows if row.get("crop_id") in allowed] if allowed else []
    ranked = rank_mix_candidates(scoped_rows, strategy=strategy)
    result = allocate_mix(
        candidates=ranked,
        tiles=int(tiles or 0),
        budget=budget,
        cap_percent=int(cap_percent),
        top_n=int(top_n),
    )
    summary = summarize_mix(result)

    cards = _build_kpi_cards(summary["totals"])
    treemap = _build_field_map(summary["allocations"], summary["totals"])
    budget_chart = _build_budget_chart(summary["allocations"], summary["totals"])
    table_rows = _format_table_rows(summary["table_rows"])
    return cards, treemap, budget_chart, table_rows


def _build_kpi_cards(totals: dict) -> list[html.Div]:
    cards = [
        ("Total seed cost", f"{totals.get('total_seed_cost', 0):,.0f}g"),
        ("Expected revenue", f"{totals.get('total_revenue', 0):,.0f}g"),
        ("Expected profit", f"{totals.get('total_profit', 0):,.0f}g"),
        ("Remaining budget", _remaining_budget_label(totals)),
        ("Unused tiles", f"{int(totals.get('unused_tiles', 0))}"),
    ]
    nodes = []
    for title, value in cards:
        nodes.append(
            html.Div(
                className="detail-card",
                children=[html.P(title, className="metric-label"), html.H3(value)],
            )
        )
    return nodes


def _remaining_budget_label(totals: dict) -> str:
    if not totals.get("budget_limited", True):
        return "Unlimited"
    return f"{totals.get('budget_remaining', 0):,.0f}g"


def _build_field_map(allocations: list[dict], totals: dict) -> go.Figure:
    if not allocations:
        return _empty_figure("No feasible crop mix under current constraints.")

    labels = [item["crop_name"] for item in allocations]
    values = [int(item["tiles"]) for item in allocations]
    parents = ["Planting Mix" for _ in allocations]
    profits = [float(item["profit"]) for item in allocations]
    seed_costs = [float(item["seed_cost"]) for item in allocations]
    colors = _palette()[: len(allocations)]

    unused_tiles = int(totals.get("unused_tiles", 0))
    if unused_tiles > 0:
        labels.append("Unused")
        values.append(unused_tiles)
        parents.append("Planting Mix")
        profits.append(0.0)
        seed_costs.append(0.0)
        colors.append("#dfe7ee")

    figure = go.Figure(
        go.Treemap(
            labels=["Planting Mix", *labels],
            parents=["", *parents],
            values=[sum(values), *values],
            branchvalues="total",
            marker={"colors": ["#f6f9fc", *colors], "line": {"color": "#ffffff", "width": 2}},
            customdata=[[0.0, 0.0], *[[profit, seed_cost] for profit, seed_cost in zip(profits, seed_costs, strict=True)]],
            hovertemplate=(
                "<b>%{label}</b><br>Tiles: %{value}<br>Profit: %{customdata[0]:,.0f}g<br>"
                "Seed cost: %{customdata[1]:,.0f}g<extra></extra>"
            ),
            texttemplate="%{label}<br>%{value} tiles",
        )
    )
    figure.update_layout(
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#24384a", "family": "Inter, Segoe UI, sans-serif", "size": 12},
    )
    return figure


def _build_budget_chart(allocations: list[dict], totals: dict) -> go.Figure:
    if not allocations:
        return _empty_figure("No allocation to display.")

    palette = _palette()
    figure = go.Figure()
    for index, item in enumerate(allocations):
        figure.add_bar(
            name=item["crop_name"],
            y=["Budget"],
            x=[float(item["seed_cost"])],
            orientation="h",
            marker={"color": palette[index % len(palette)], "line": {"color": "#ffffff", "width": 1}},
            hovertemplate=f"{item['crop_name']} seed cost: %{{x:,.0f}}g<extra></extra>",
        )

    remaining = float(totals.get("budget_remaining", 0.0) or 0.0)
    if totals.get("budget_limited", True) and remaining > 0:
        figure.add_bar(
            name="Remaining",
            y=["Budget"],
            x=[remaining],
            orientation="h",
            marker={"color": "#dfe7ee", "line": {"color": "#ffffff", "width": 1}},
            hovertemplate="Remaining budget: %{x:,.0f}g<extra></extra>",
        )

    figure.update_layout(
        barmode="stack",
        margin={"l": 12, "r": 12, "t": 18, "b": 48},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": -0.18},
        xaxis={"title": "Gold", "fixedrange": True, "gridcolor": "#e4ebf2", "ticksuffix": "g"},
        yaxis={"fixedrange": True, "showticklabels": False},
        font={"color": "#24384a", "family": "Inter, Segoe UI, sans-serif", "size": 12},
    )
    return figure


def _palette() -> list[str]:
    return ["#1497ee", "#23a67a", "#ff334a", "#f39c12", "#536679", "#9b7cff", "#00a6a6", "#c26a2e"]


def _format_table_rows(rows: list[dict]) -> list[dict]:
    formatted = []
    for row in rows:
        formatted.append(
            {
                "crop_name": row["crop_name"],
                "tiles": int(row["tiles"]),
                "seed_cost": f"{row['seed_cost']:,.0f}g",
                "harvest_count": int(row["harvest_count"]),
                "revenue": f"{row['revenue']:,.0f}g",
                "profit": f"{row['profit']:,.0f}g",
                "profit_per_day": f"{row['profit_per_day']:,.1f}g",
                "roi": f"{row['roi']:.2f}",
            }
        )
    return formatted


def _empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    figure.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    return figure
