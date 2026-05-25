from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State, callback, dash_table, dcc, html, no_update, register_page

from src.figures import CHART_COLORS, axis_style, base_layout
from src.processing_math import (
    EQUIPMENT_KEG,
    EQUIPMENT_MILL,
    EQUIPMENT_NONE,
    EQUIPMENT_OIL_MAKER,
    EQUIPMENT_PRESERVES_JAR,
    build_processing_methods,
    evaluate_processing_capacity,
)

register_page(__name__, path="/processing-lab", name="Processing Lab", order=4)

TABLE_COLUMNS = [
    {"name": "Method", "id": "method_name"},
    {"name": "Product", "id": "product_name"},
    {"name": "Equipment", "id": "equipment"},
    {"name": "Unit Value", "id": "unit_value"},
    {"name": "Processed Units", "id": "processed_units"},
    {"name": "Leftover Raw", "id": "leftover_units"},
    {"name": "Total Revenue", "id": "total_revenue"},
    {"name": "Profit", "id": "profit"},
    {"name": "Extra vs Raw", "id": "extra_revenue"},
]

MAX_PROCESSING_HORIZON_DAYS = 365

EQUIPMENT_LABELS = {
    EQUIPMENT_NONE: "None",
    EQUIPMENT_KEG: "Keg",
    EQUIPMENT_PRESERVES_JAR: "Preserves Jar",
    EQUIPMENT_MILL: "Mill",
    EQUIPMENT_OIL_MAKER: "Oil Maker",
}


def _control_field(title: str, body: object, class_name: str = "control-field") -> html.Div:
    return html.Div(
        className=class_name,
        children=[
            html.Label(title, className="control-label"),
            body,
        ],
    )


layout = html.Div(
    className="page-card processing-page",
    children=[
        html.Div(
            className="page-head",
            children=[
                html.P("Value add workspace", className="badge"),
                html.H2("Processing Lab"),
                html.P("Compare raw sales against Stardew processing methods and equipment limits."),
            ],
        ),
        html.Section(
            className="plan-section processing-recommendation-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Best Processing Path"),
                        html.P("The recommendation accounts for machine throughput and leftover raw crop sales."),
                    ],
                ),
                html.Div(id="processing-recommendation", className="processing-recommendation"),
            ],
        ),
        html.Section(
            className="plan-section processing-controls-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Setup"),
                        html.P("Tune equipment capacity for this page only."),
                    ],
                ),
                html.Div(
                    className="processing-control-grid",
                    children=[
                        _control_field(
                            "Crop",
                            dcc.Dropdown(
                                id="processing-crop-select",
                                options=[],
                                clearable=False,
                                placeholder="Select crop",
                            ),
                            class_name="control-field processing-crop-field",
                        ),
                        _control_field(
                            "Kegs",
                            dcc.Input(
                                id="processing-kegs",
                                type="number",
                                min=0,
                                step=1,
                                value=8,
                                className="control-input",
                            ),
                        ),
                        _control_field(
                            "Jars",
                            dcc.Input(
                                id="processing-jars",
                                type="number",
                                min=0,
                                step=1,
                                value=8,
                                className="control-input",
                            ),
                        ),
                        _control_field(
                            "Oil makers",
                            dcc.Input(
                                id="processing-oil-makers",
                                type="number",
                                min=0,
                                step=1,
                                value=2,
                                className="control-input",
                            ),
                        ),
                        html.Div(
                            className="processing-toggle-row",
                            children=[
                                dcc.Checklist(
                                    id="processing-mill-available",
                                    options=[{"label": "Mill available", "value": "yes"}],
                                    value=["yes"],
                                    className="inline-checklist",
                                    inputClassName="inline-checklist-input",
                                    labelClassName="inline-checklist-label",
                                ),
                                dcc.Checklist(
                                    id="processing-artisan",
                                    options=[{"label": "Artisan profession", "value": "yes"}],
                                    value=[],
                                    className="inline-checklist",
                                    inputClassName="inline-checklist-input",
                                    labelClassName="inline-checklist-label",
                                ),
                            ],
                        ),
                        _control_field(
                            "Processing horizon",
                            dcc.Slider(
                                id="processing-horizon",
                                min=1,
                                max=MAX_PROCESSING_HORIZON_DAYS,
                                step=1,
                                value=28,
                                marks={1: "1", 28: "28", 84: "84", 168: "168", 365: "365"},
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                            class_name="control-field processing-horizon-field",
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className="processing-chart-grid",
            children=[
                html.Section(
                    className="plan-section processing-chart-wide",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Value Runway"),
                                html.P("Per-unit method value against the raw crop baseline."),
                            ],
                        ),
                        dcc.Graph(
                            id="processing-value-chart",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "360px"},
                        ),
                    ],
                ),
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Revenue Lift Map"),
                                html.P("Total revenue versus extra gold after equipment limits."),
                            ],
                        ),
                        dcc.Graph(
                            id="processing-extra-chart",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "330px"},
                        ),
                    ],
                ),
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Throughput Strip"),
                                html.P("Used cycles and idle capacity by machine path."),
                            ],
                        ),
                        dcc.Graph(
                            id="processing-bottleneck-chart",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "330px"},
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
                        html.H3("Method Table"),
                        html.P("Capacity and revenue calculations by available method."),
                    ],
                ),
                dash_table.DataTable(
                    id="processing-method-table",
                    columns=TABLE_COLUMNS,
                    data=[],
                    sort_action="native",
                    page_action="none",
                    fixed_rows={"headers": True},
                    style_as_list_view=True,
                    style_table={
                        "overflowX": "auto",
                        "overflowY": "auto",
                        "maxHeight": "360px",
                        "width": "100%",
                        "maxWidth": "100%",
                    },
                    style_cell={
                        "fontFamily": "Inter, Segoe UI, sans-serif",
                        "fontSize": 13,
                        "maxWidth": 170,
                        "minWidth": 95,
                        "overflow": "hidden",
                        "padding": "8px",
                        "textOverflow": "ellipsis",
                    },
                    style_header={"fontFamily": "Inter, Segoe UI, sans-serif", "fontWeight": 700},
                    css=[{"selector": ".dash-spreadsheet", "rule": "max-width: 100%;"}],
                ),
                html.P(
                    "Throughput is a planning estimate. It does not simulate exact harvest-day inventory queues.",
                    className="processing-note",
                ),
            ],
        ),
    ],
)


@callback(
    Output("processing-crop-select", "options"),
    Output("processing-crop-select", "value"),
    Output("processing-horizon", "max"),
    Output("processing-horizon", "value"),
    Output("processing-horizon", "marks"),
    Input("filtered-crops-store", "data"),
    Input("selected-crop-store", "data"),
    State("processing-crop-select", "value"),
)
def sync_processing_selection(rows: list[dict] | None, selected_crop: dict | None, current_value: int | None):
    rows = rows or []
    if not rows:
        return [], None, MAX_PROCESSING_HORIZON_DAYS, 28, {1: "1", 28: "28", 84: "84", 168: "168", 365: "365"}

    options = [{"label": row["crop_name"], "value": row["crop_id"]} for row in rows]
    valid_ids = {row["crop_id"] for row in rows}
    selected_id = selected_crop.get("crop_id") if selected_crop else None
    value = selected_id if selected_id in valid_ids else current_value
    if value not in valid_ids:
        value = rows[0]["crop_id"]

    row = _find_row(rows, value) or rows[0]
    default_horizon = max(1, int(row.get("window_days", 28)))
    chosen = _safe_int(current_value, default=default_horizon)
    chosen = min(MAX_PROCESSING_HORIZON_DAYS, max(1, chosen))
    marks = {1: "1", 28: "28", 84: "84", 168: "168", 365: "365"}
    return options, value, MAX_PROCESSING_HORIZON_DAYS, chosen, marks


@callback(
    Output("selected-crop-store", "data", allow_duplicate=True),
    Input("processing-crop-select", "value"),
    State("filtered-crops-store", "data"),
    prevent_initial_call=True,
)
def sync_processing_crop_to_store(crop_id: str | None, rows: list[dict] | None):
    if not crop_id:
        return no_update
    row = _find_row(rows or [], crop_id)
    return row if row else no_update


@callback(
    Output("processing-recommendation", "children"),
    Output("processing-value-chart", "figure"),
    Output("processing-extra-chart", "figure"),
    Output("processing-bottleneck-chart", "figure"),
    Output("processing-method-table", "data"),
    Input("processing-crop-select", "value"),
    Input("filtered-crops-store", "data"),
    Input("processing-kegs", "value"),
    Input("processing-jars", "value"),
    Input("processing-oil-makers", "value"),
    Input("processing-mill-available", "value"),
    Input("processing-artisan", "value"),
    Input("processing-horizon", "value"),
    Input("processing-control", "value"),
    State("tiles-control", "value"),
)
def update_processing_lab(
    crop_id: str | None,
    rows: list[dict] | None,
    kegs: int | None,
    jars: int | None,
    oil_makers: int | None,
    mill_available: list[str] | None,
    artisan_value: list[str] | None,
    horizon_days: int | None,
    processing_mode: str | None,
    tiles: int | None,
):
    row = _find_row(rows or [], crop_id)
    if row is None:
        empty = _empty_figure("Select a crop to compare processing methods.")
        return [html.H3("No crop selected"), html.P("Choose a crop to begin.")], empty, empty, empty, []

    artisan = "yes" in (artisan_value or []) or processing_mode == "artisan"
    raw_units = _raw_units(row, tiles)
    raw_price = float(row["sell_price_raw"])
    methods = build_processing_methods(row["crop_name"], raw_price, artisan=artisan)
    if processing_mode == "raw_only":
        methods = [method for method in methods if method["equipment"] == EQUIPMENT_NONE]
    equipment_counts = {
        EQUIPMENT_NONE: 0,
        EQUIPMENT_KEG: _safe_int(kegs),
        EQUIPMENT_PRESERVES_JAR: _safe_int(jars),
        EQUIPMENT_MILL: 1 if "yes" in (mill_available or []) else 0,
        EQUIPMENT_OIL_MAKER: _safe_int(oil_makers),
    }
    evaluated = [
        evaluate_processing_capacity(
            method=method,
            raw_units=raw_units,
            raw_unit_price=raw_price,
            machine_count=equipment_counts.get(method["equipment"], 0),
            horizon_days=_safe_int(horizon_days, default=int(row.get("window_days", 28))),
        )
        for method in methods
    ]
    best = max(evaluated, key=lambda item: (item["total_revenue"], item["unit_value"], item["method_name"]))

    return (
        _build_recommendation(row, raw_units, best),
        _build_value_ladder(methods),
        _build_extra_chart(evaluated),
        _build_utilization_chart(evaluated),
        _build_table_rows(evaluated, seed_cost=float(row.get("seed_cost", 0))),
    )


def _build_value_ladder(methods: list[dict]) -> go.Figure:
    raw_value = next(method["value_per_input"] for method in methods if method["method_id"] == "raw")
    ranked = sorted(methods, key=lambda method: method["value_per_input"], reverse=True)
    labels = [_short_method_label(method) for method in ranked]
    values = [float(method["value_per_input"]) for method in ranked]
    lift_values = [value - raw_value for value in values]
    max_value = max(values)
    left_padding = max_value * 0.02
    right_padding = max_value * 0.16

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker={
                "color": [_method_color(method) for method in ranked],
                "line": {"color": CHART_COLORS["cream"], "width": 1},
            },
            width=0.58,
            text=[f"{value:,.0f}g" for value in values],
            textposition="outside",
            cliponaxis=False,
            customdata=[
                [
                    _method_label(method),
                    lift,
                    method["value_per_input"] / raw_value if raw_value else 0,
                ]
                for method, lift in zip(ranked, lift_values, strict=True)
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Value: %{x:,.1f}g per raw unit<br>"
                "Lift vs raw: %{customdata[1]:+,.1f}g<br>"
                "Multiplier: %{customdata[2]:.2f}x<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[raw_value for _ in ranked],
            y=labels,
            mode="markers",
            marker={"symbol": "line-ns-open", "size": 22, "color": CHART_COLORS["ink"], "line": {"width": 3}},
            name="Raw baseline",
            hovertemplate="Raw baseline: %{x:,.1f}g<extra></extra>",
        )
    )
    for label, value, lift in zip(labels, values, lift_values, strict=True):
        if lift > 0:
            figure.add_shape(
                type="line",
                x0=raw_value,
                x1=value,
                y0=label,
                y1=label,
                xref="x",
                yref="y",
                line={"color": CHART_COLORS["tan"], "width": 10},
                layer="below",
            )

    figure.add_vline(
        x=raw_value,
        line_color=CHART_COLORS["ink"],
        line_dash="dot",
        line_width=1,
        opacity=0.58,
        annotation_text="raw",
        annotation_position="top",
        annotation_font={"size": 11, "color": CHART_COLORS["muted"]},
    )
    figure.update_layout(
        **base_layout(height=max(360, 138 + (len(ranked) * 54)), margin={"l": 126, "r": 72, "t": 24, "b": 54}),
        showlegend=False,
        bargap=0.38,
        xaxis={
            **axis_style("Gold per Raw Unit", ticksuffix="g"),
            "range": [max(0, min(values) - left_padding), max_value + right_padding],
        },
        yaxis={"automargin": True, "fixedrange": True, "autorange": "reversed", "tickfont": {"size": 12}},
    )
    return figure


def _build_extra_chart(evaluated: list[dict]) -> go.Figure:
    ranked = sorted(
        [item for item in evaluated if item["equipment"] != EQUIPMENT_NONE],
        key=lambda item: item["extra_revenue"],
        reverse=True,
    )
    if not ranked:
        return _empty_figure("This crop has no processing methods beyond raw sale.")

    max_processed = max(float(item["processed_units"]) for item in ranked) or 1
    figure = go.Figure(
        go.Scatter(
            x=[item["total_revenue"] for item in ranked],
            y=[item["extra_revenue"] for item in ranked],
            mode="markers+text",
            text=[_short_method_label(item) for item in ranked],
            textposition="top center",
            marker={
                "size": [max(18, min(56, 18 + (float(item["processed_units"]) / max_processed) * 38)) for item in ranked],
                "color": [item["extra_revenue"] for item in ranked],
                "colorscale": [[0, CHART_COLORS["red"]], [0.45, CHART_COLORS["gold"]], [1, CHART_COLORS["green"]]],
                "cmin": min(0, min(item["extra_revenue"] for item in ranked)),
                "cmax": max(1, max(item["extra_revenue"] for item in ranked)),
                "line": {"color": CHART_COLORS["cream"], "width": 2},
                "opacity": 0.9,
                "showscale": False,
            },
            customdata=[
                [
                    _method_label(item),
                    item["processed_units"],
                    item["leftover_units"],
                    item["unit_value"],
                ]
                for item in ranked
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Total revenue: %{x:,.0f}g<br>"
                "Extra vs raw: %{y:,.0f}g<br>"
                "Processed units: %{customdata[1]:,.0f}<br>"
                "Leftover raw: %{customdata[2]:,.0f}<br>"
                "Unit value: %{customdata[3]:,.1f}g<extra></extra>"
            ),
        )
    )
    figure.add_hline(y=0, line_color=CHART_COLORS["brown"], line_dash="dot", line_width=1)
    figure.update_layout(
        **base_layout(height=max(350, 310 + (len(ranked) * 7)), margin={"l": 66, "r": 38, "t": 22, "b": 58}),
        showlegend=False,
        xaxis=axis_style("Total Revenue", ticksuffix="g"),
        yaxis=axis_style("Extra Gold vs Raw", ticksuffix="g"),
    )
    return figure


def _build_utilization_chart(evaluated: list[dict]) -> go.Figure:
    methods = [item for item in evaluated if item["equipment"] != EQUIPMENT_NONE and item["machine_cycles"] > 0]
    if not methods:
        return _empty_figure("No available machine cycles for this crop and setup.")

    methods = sorted(methods, key=lambda item: item["processed_batches"] / item["machine_cycles"], reverse=True)
    labels = [_short_method_label(item) for item in methods]
    used = [item["processed_batches"] for item in methods]
    idle = [max(0, item["machine_cycles"] - item["processed_batches"]) for item in methods]
    utilization = [(item["processed_batches"] / item["machine_cycles"]) * 100 for item in methods]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            name="Used cycles",
            y=labels,
            x=used,
            orientation="h",
            marker={"color": CHART_COLORS["green"], "line": {"color": CHART_COLORS["cream"], "width": 1}},
            text=[f"{value:,.0f}" for value in used],
            textposition="inside",
            insidetextanchor="middle",
            customdata=utilization,
            hovertemplate="%{y}<br>Used cycles: %{x:,.0f}<br>Utilization: %{customdata:.0f}%<extra></extra>",
        )
    )
    figure.add_trace(
        go.Bar(
            name="Idle cycles",
            y=labels,
            x=idle,
            orientation="h",
            marker={"color": CHART_COLORS["tan"], "line": {"color": CHART_COLORS["cream"], "width": 1}},
            text=[f"{value:,.0f}" if value else "" for value in idle],
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate="%{y}<br>Idle cycles: %{x:,.0f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            name="Utilization",
            x=[item["machine_cycles"] for item in methods],
            y=labels,
            mode="markers+text",
            marker={"size": 13, "color": CHART_COLORS["gold"], "line": {"color": CHART_COLORS["cream"], "width": 2}},
            text=[f"{value:.0f}%" for value in utilization],
            textposition="middle right",
            hovertemplate="%{y}<br>Total cycles: %{x:,.0f}<extra></extra>",
        )
    )
    figure.update_layout(
        **base_layout(height=max(330, 116 + (len(methods) * 54)), margin={"l": 118, "r": 62, "t": 22, "b": 50}),
        barmode="stack",
        legend={"orientation": "h", "x": 0, "y": 1.08, "font": {"size": 11}},
        xaxis=axis_style("Machine Cycles"),
        yaxis={"automargin": True, "fixedrange": True, "autorange": "reversed", "tickfont": {"size": 12}},
    )
    return figure


def _build_recommendation(row: dict, raw_units: float, best: dict) -> list[object]:
    equipment = EQUIPMENT_LABELS.get(best["equipment"], best["equipment"])
    processed_share = 0 if raw_units <= 0 else min(100, (best["processed_units"] / raw_units) * 100)
    leftover_share = max(0, 100 - processed_share)
    return [
        html.Div(
            className="processing-recommendation-head",
            children=[
                html.Div(
                    children=[
                        html.P("Best available method", className="badge"),
                        html.H3(f"{best['method_name']}: {best['product_name']}"),
                    ]
                ),
                html.Div(
                    className="processing-recommendation-total",
                    children=[
                        html.Span("Total revenue"),
                        html.Strong(f"{best['total_revenue']:,.0f}g"),
                    ],
                ),
            ],
        ),
        html.Div(
            className="processing-flow-summary",
            children=[
                html.Div(
                    className="processing-flow-item",
                    children=[
                        html.Span("Processed share", className="metric-label"),
                        html.Strong(f"{processed_share:.0f}%", className="metric-value"),
                    ],
                ),
                html.Div(
                    className="processing-flow-item",
                    children=[
                        html.Span("Leftover raw", className="metric-label"),
                        html.Strong(f"{leftover_share:.0f}%", className="metric-value"),
                    ],
                ),
                html.Div(
                    className="processing-flow-item",
                    children=[
                        html.Span("Revenue lift", className="metric-label"),
                        html.Strong(f"{best['extra_revenue']:,.0f}g", className="metric-value"),
                    ],
                ),
            ],
        ),
        html.Div(
            className="metric-grid processing-metric-grid",
            children=[
                _metric_tile("Crop", row["crop_name"]),
                _metric_tile("Raw units", f"{raw_units:,.0f}"),
                _metric_tile("Equipment", equipment),
                _metric_tile("Processed", f"{best['processed_units']:,.0f} units"),
                _metric_tile("Leftover raw", f"{best['leftover_units']:,.0f} units"),
                _metric_tile("Extra vs raw", f"{best['extra_revenue']:,.0f}g"),
            ],
        ),
    ]


def _short_method_label(method: dict) -> str:
    if method["method_id"] == "raw":
        return "Raw"
    return method["method_name"]


def _method_label(method: dict) -> str:
    return f"{method['method_name']} ({method['product_name']})"


def _method_color(method: dict) -> str:
    equipment = method.get("equipment")
    if equipment == EQUIPMENT_NONE:
        return CHART_COLORS["tan"]
    if equipment == EQUIPMENT_KEG:
        return CHART_COLORS["gold"]
    if equipment == EQUIPMENT_PRESERVES_JAR:
        return CHART_COLORS["green"]
    if equipment == EQUIPMENT_MILL:
        return CHART_COLORS["brown"]
    if equipment == EQUIPMENT_OIL_MAKER:
        return CHART_COLORS["red"]
    return CHART_COLORS["muted"]


def _metric_tile(label: str, value: str) -> html.Div:
    return html.Div(
        className="metric-tile",
        children=[html.Span(label, className="metric-label"), html.Strong(value, className="metric-value")],
    )


def _build_table_rows(evaluated: list[dict], seed_cost: float) -> list[dict]:
    rows = []
    for item in evaluated:
        rows.append(
            {
                "method_name": item["method_name"],
                "product_name": item["product_name"],
                "equipment": EQUIPMENT_LABELS.get(item["equipment"], item["equipment"]),
                "unit_value": f"{item['unit_value']:,.1f}g",
                "processed_units": f"{item['processed_units']:,.0f}",
                "leftover_units": f"{item['leftover_units']:,.0f}",
                "total_revenue": f"{item['total_revenue']:,.0f}g",
                "profit": f"{item['total_revenue'] - seed_cost:,.0f}g",
                "extra_revenue": f"{item['extra_revenue']:,.0f}g",
            }
        )
    return sorted(rows, key=lambda item: float(item["extra_revenue"].replace("g", "").replace(",", "")), reverse=True)


def _empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        **base_layout(height=300, margin={"l": 20, "r": 20, "t": 20, "b": 20}),
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    figure.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    return figure


def _find_row(rows: list[dict], crop_id: str | None) -> dict | None:
    if not crop_id:
        return None
    for row in rows:
        if row.get("crop_id") == crop_id:
            return row
    return None


def _raw_units(row: dict, tiles: int | None) -> float:
    tile_count = _safe_int(tiles, default=0)
    return float(row.get("harvest_count", 0)) * float(row.get("yield_per_harvest", row.get("base_yield", 1))) * tile_count


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default
