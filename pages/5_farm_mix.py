from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State, callback, dash_table, dcc, html, register_page

from src.farm_mix import allocate_mix, rank_mix_candidates, summarize_mix
from src.figures import CHART_COLORS, CHART_PALETTE, base_layout

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
                                html.H3("Budget Flow"),
                                html.P("Money flow from available budget into seed spend and expected return."),
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
        colors.append(CHART_COLORS["tan"])

    figure = go.Figure(
        go.Treemap(
            labels=["Planting Mix", *labels],
            parents=["", *parents],
            values=[sum(values), *values],
            branchvalues="total",
            marker={"colors": [CHART_COLORS["cream"], *colors], "line": {"color": CHART_COLORS["cream"], "width": 2}},
            customdata=[[0.0, 0.0], *[[profit, seed_cost] for profit, seed_cost in zip(profits, seed_costs, strict=True)]],
            hovertemplate=(
                "<b>%{label}</b><br>Tiles: %{value}<br>Profit: %{customdata[0]:,.0f}g<br>"
                "Seed cost: %{customdata[1]:,.0f}g<extra></extra>"
            ),
            texttemplate="%{label}<br>%{value} tiles",
        )
    )
    figure.update_layout(
        **base_layout(height=460, margin={"l": 8, "r": 8, "t": 8, "b": 8}),
    )
    return figure


def _build_budget_chart(allocations: list[dict], totals: dict) -> go.Figure:
    if not allocations:
        return _empty_figure("No allocation to display.")

    labels = ["Budget", *[item["crop_name"] for item in allocations], "Remaining", "Expected Profit"]
    budget_index = 0
    remaining_index = len(labels) - 2
    profit_index = len(labels) - 1
    source = []
    target = []
    value = []
    colors = []
    palette = _palette()

    for index, item in enumerate(allocations, start=1):
        crop_color = palette[(index - 1) % len(palette)]
        seed_cost = float(item["seed_cost"])
        expected_profit = max(0.0, float(item["profit"]))

        source.append(budget_index)
        target.append(index)
        value.append(seed_cost)
        colors.append(crop_color)

        source.append(index)
        target.append(profit_index)
        value.append(expected_profit)
        colors.append("rgba(79, 138, 61, 0.34)")

    remaining = float(totals.get("budget_remaining", 0.0) or 0.0)
    if totals.get("budget_limited", True) and remaining > 0:
        source.append(budget_index)
        target.append(remaining_index)
        value.append(remaining)
        colors.append("rgba(117, 104, 82, 0.24)")

    node_colors = [
        CHART_COLORS["brown"],
        *[palette[index % len(palette)] for index in range(len(allocations))],
        CHART_COLORS["tan"],
        CHART_COLORS["green"],
    ]
    figure = go.Figure(
        go.Sankey(
            arrangement="snap",
            node={
                "label": labels,
                "pad": 18,
                "thickness": 16,
                "line": {"color": CHART_COLORS["cream"], "width": 1},
                "color": node_colors,
            },
            link={
                "source": source,
                "target": target,
                "value": value,
                "color": colors,
                "hovertemplate": "%{source.label} -> %{target.label}<br>%{value:,.0f}g<extra></extra>",
            },
        )
    )

    figure.update_layout(
        **base_layout(height=380, margin={"l": 8, "r": 8, "t": 8, "b": 8}),
    )
    return figure


def _palette() -> list[str]:
    return CHART_PALETTE


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
        **base_layout(height=320, margin={"l": 20, "r": 20, "t": 20, "b": 20}),
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    figure.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    return figure
