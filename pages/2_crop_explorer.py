from __future__ import annotations

import math
from typing import Any

import plotly.graph_objects as go
from dash import Input, Output, State, callback, dash_table, dcc, html, no_update, register_page

register_page(__name__, path="/crop-explorer", name="Crop Explorer", order=2)

AXIS_OPTIONS = [
    {"label": "Seed Price", "value": "seed_price"},
    {"label": "Profit per Day", "value": "profit_per_day"},
    {"label": "Total Profit", "value": "profit_total"},
    {"label": "ROI", "value": "roi"},
    {"label": "Growth Days", "value": "growth_days"},
    {"label": "First Harvest", "value": "first_harvest_day"},
    {"label": "Harvest Count", "value": "harvest_count"},
]

AXIS_LABELS = {option["value"]: option["label"] for option in AXIS_OPTIONS}

COLOR_OPTIONS = [
    {"label": "Season", "value": "season"},
    {"label": "Regrowable", "value": "is_regrowable"},
    {"label": "Trellis", "value": "is_trellis"},
    {"label": "Affordable", "value": "affordable"},
    {"label": "Maturity", "value": "can_mature"},
]

HISTOGRAM_OPTIONS = [
    {"label": "Profit per Day", "value": "profit_per_day"},
    {"label": "ROI", "value": "roi"},
    {"label": "Growth Days", "value": "growth_days"},
    {"label": "Seed Price", "value": "seed_price"},
]

TABLE_COLUMNS = [
    {"name": "Crop", "id": "crop_name"},
    {"name": "Season", "id": "season"},
    {"name": "Seed", "id": "seed_price"},
    {"name": "Growth", "id": "growth_days"},
    {"name": "Harvests", "id": "harvest_count"},
    {"name": "Profit", "id": "profit_total"},
    {"name": "Profit/Day", "id": "profit_per_day"},
    {"name": "ROI", "id": "roi"},
    {"name": "Affordable", "id": "affordable"},
]

COLOR_PALETTE = ["#1497ee", "#ff334a", "#23a67a", "#9b7cff", "#f39c12", "#536679"]
PLOTLY_COLORS = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]


def _control_field(title: str, body: object) -> html.Div:
    return html.Div(
        className="control-field",
        children=[
            html.Label(title, className="control-label"),
            body,
        ],
    )


layout = html.Div(
    className="page-card explorer-page",
    children=[
        html.Div(
            className="page-head",
            children=[
                html.P("Comparison workspace", className="badge"),
                html.H2("Crop Explorer"),
                html.P("Explore crop trade-offs visually and inspect why one crop beats another."),
            ],
        ),
        html.Section(
            className="plan-section explorer-controls-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Explore Trade-offs"),
                        html.P("Change axes, color grouping, and affordability scope."),
                    ],
                ),
                html.Div(
                    className="explorer-control-grid",
                    children=[
                        _control_field(
                            "X-axis",
                            dcc.Dropdown(
                                id="explorer-x-axis",
                                options=AXIS_OPTIONS,
                                value="seed_price",
                                clearable=False,
                            ),
                        ),
                        _control_field(
                            "Y-axis",
                            dcc.Dropdown(
                                id="explorer-y-axis",
                                options=AXIS_OPTIONS,
                                value="profit_per_day",
                                clearable=False,
                            ),
                        ),
                        _control_field(
                            "Color by",
                            dcc.Dropdown(
                                id="explorer-color-by",
                                options=COLOR_OPTIONS,
                                value="season",
                                clearable=False,
                            ),
                        ),
                        html.Div(
                            className="explorer-toggle-row",
                            children=[
                                dcc.Checklist(
                                    id="explorer-affordable-only",
                                    options=[{"label": "Affordable only", "value": "yes"}],
                                    value=[],
                                    className="inline-checklist",
                                    inputClassName="inline-checklist-input",
                                    labelClassName="inline-checklist-label",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className="explorer-main-grid",
            children=[
                html.Section(
                    className="plan-section explorer-scatter-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Crop Map"),
                                html.P("Click a point to select a crop."),
                            ],
                        ),
                        dcc.Graph(
                            id="explorer-scatter",
                            className="explorer-scatter",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "520px"},
                        ),
                    ],
                ),
                html.Section(
                    className="plan-section explorer-side-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Selected Crop Benchmark"),
                                html.P(id="explorer-filter-status"),
                            ],
                        ),
                        html.Div(id="explorer-benchmark", className="explorer-benchmark"),
                        html.Div(id="explorer-comparison-panel", className="detail-card explorer-comparison-card"),
                    ],
                ),
            ],
        ),
        html.Section(
            className="plan-section explorer-histogram-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.Div(
                            children=[
                                html.H3("Metric Distribution"),
                                html.P("See whether the selected crop is typical or an outlier among visible crops."),
                            ],
                        ),
                        dcc.Dropdown(
                            id="explorer-histogram-metric",
                            options=HISTOGRAM_OPTIONS,
                            value="profit_per_day",
                            clearable=False,
                            className="histogram-metric-control",
                        ),
                    ],
                ),
                dcc.Graph(
                    id="explorer-histogram",
                    config={"displayModeBar": False, "responsive": True},
                    style={"height": "320px"},
                ),
            ],
        ),
        html.Section(
            className="plan-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Filtered Crops"),
                        html.P("The table follows local explorer filters and selection."),
                    ],
                ),
                dash_table.DataTable(
                    id="explorer-crop-table",
                    columns=TABLE_COLUMNS,
                    data=[],
                    row_selectable="single",
                    selected_rows=[],
                    sort_action="native",
                    filter_action="native",
                    page_size=8,
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
    Output("explorer-scatter", "figure"),
    Output("explorer-benchmark", "children"),
    Output("explorer-comparison-panel", "children"),
    Output("explorer-histogram", "figure"),
    Output("explorer-crop-table", "data"),
    Output("explorer-crop-table", "selected_rows"),
    Output("explorer-filter-status", "children"),
    Input("filtered-crops-store", "data"),
    Input("selected-crop-store", "data"),
    Input("explorer-x-axis", "value"),
    Input("explorer-y-axis", "value"),
    Input("explorer-color-by", "value"),
    Input("explorer-affordable-only", "value"),
    Input("explorer-histogram-metric", "value"),
)
def update_explorer(
    rows: list[dict] | None,
    selected_crop: dict | None,
    x_axis: str,
    y_axis: str,
    color_by: str,
    affordable_only: list[str] | None,
    histogram_metric: str,
):
    scoped_rows = _apply_local_filters(
        rows=rows or [],
        affordable_only="yes" in (affordable_only or []),
    )

    selected_crop_id = selected_crop.get("crop_id") if selected_crop else None
    if scoped_rows and not any(row["crop_id"] == selected_crop_id for row in scoped_rows):
        selected_crop_id = scoped_rows[0]["crop_id"]
        selected_crop = scoped_rows[0]

    scatter = _build_scatter(scoped_rows, selected_crop_id, x_axis, y_axis, color_by)
    benchmark = _build_benchmark(scoped_rows, selected_crop)
    comparison = _build_comparison_panel(scoped_rows, selected_crop)
    histogram = _build_histogram(scoped_rows, selected_crop, histogram_metric)
    table_rows = [_to_table_row(row) for row in scoped_rows]
    selected_rows = _selected_table_rows(table_rows, selected_crop_id)
    status = _benchmark_status(scoped_rows, selected_crop)

    return scatter, benchmark, comparison, histogram, table_rows, selected_rows, status


@callback(
    Output("selected-crop-store", "data", allow_duplicate=True),
    Input("explorer-scatter", "clickData"),
    State("filtered-crops-store", "data"),
    prevent_initial_call=True,
)
def select_crop_from_scatter(click_data: dict | None, rows: list[dict] | None):
    crop_id = _clicked_crop_id(click_data)
    if crop_id is None:
        return no_update

    for row in rows or []:
        if row.get("crop_id") == crop_id:
            return row
    return no_update


@callback(
    Output("selected-crop-store", "data", allow_duplicate=True),
    Input("explorer-crop-table", "derived_virtual_data"),
    Input("explorer-crop-table", "derived_virtual_selected_rows"),
    prevent_initial_call=True,
)
def select_crop_from_explorer_table(visible_rows: list[dict] | None, selected_rows: list[int] | None):
    rows = visible_rows or []
    if not rows:
        return no_update

    selected_index = selected_rows[0] if selected_rows else 0
    selected_index = max(0, min(selected_index, len(rows) - 1))
    return rows[selected_index]


def _apply_local_filters(
    rows: list[dict],
    affordable_only: bool,
) -> list[dict]:
    filtered = list(rows)
    if affordable_only:
        filtered = [row for row in filtered if row.get("affordable") is True]
    return filtered


def _build_scatter(rows: list[dict], selected_crop_id: str | None, x_axis: str, y_axis: str, color_by: str) -> go.Figure:
    figure = go.Figure()
    if not rows:
        return _empty_figure("No crops match the current explorer filters", height=520)

    color_groups = _group_rows(rows, color_by)
    for index, (group_name, group_rows) in enumerate(color_groups.items()):
        color = COLOR_PALETTE[index % len(COLOR_PALETTE)]
        figure.add_trace(
            go.Scatter(
                x=[row[x_axis] for row in group_rows],
                y=[row[y_axis] for row in group_rows],
                mode="markers",
                name=group_name,
                customdata=[
                    [
                        row["crop_id"],
                        row["crop_name"],
                        row["profit_total"],
                        row["profit_per_day"],
                        row["roi"],
                    ]
                    for row in group_rows
                ],
                hovertemplate=(
                    "<b>%{customdata[1]}</b><br>"
                    f"{AXIS_LABELS.get(x_axis, x_axis)}: %{{x:,.2f}}<br>"
                    f"{AXIS_LABELS.get(y_axis, y_axis)}: %{{y:,.2f}}<br>"
                    "Total profit: %{customdata[2]:,.0f}g<br>"
                    "Profit/day: %{customdata[3]:,.1f}g<br>"
                    "ROI: %{customdata[4]:.2f}<extra>Click to select</extra>"
                ),
                marker={
                    "color": color,
                    "line": {
                        "color": ["#143047" if row["crop_id"] == selected_crop_id else "#ffffff" for row in group_rows],
                        "width": [2.5 if row["crop_id"] == selected_crop_id else 1 for row in group_rows],
                    },
                    "opacity": [1 if row["crop_id"] == selected_crop_id else 0.74 for row in group_rows],
                    "size": [_marker_size(row) for row in group_rows],
                    "sizemode": "diameter",
                },
            )
        )

    figure.update_layout(
        height=520,
        margin={"l": 62, "r": 24, "t": 16, "b": 58},
        font={"color": "#24384a", "family": "Inter, Segoe UI, sans-serif", "size": 12},
        hoverlabel=_hover_label_style(),
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        uirevision=f"{x_axis}:{y_axis}:{color_by}",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=_axis_style(AXIS_LABELS.get(x_axis, x_axis)),
        yaxis=_axis_style(AXIS_LABELS.get(y_axis, y_axis)),
    )
    return figure


def _build_benchmark(rows: list[dict], selected_crop: dict | None) -> html.Div:
    if not rows or selected_crop is None:
        return html.Div(
            className="explorer-benchmark-empty",
            children="Select a crop to compare against the visible average.",
        )

    metrics = [
        ("Profit/day", "profit_per_day", True, "g/day"),
        ("Total profit", "profit_total", True, "g"),
        ("ROI", "roi", True, "x"),
        ("Speed", "growth_days", False, "days"),
        ("Low seed cost", "seed_price", False, "g"),
        ("Harvests", "harvest_count", True, ""),
    ]
    deltas = [_signed_percent_delta(rows, selected_crop, key, high_is_good) for _, key, high_is_good, _ in metrics]
    selected_values = [_format_raw_metric(float(selected_crop[key]), suffix) for _, key, _, suffix in metrics]
    average_values = [_format_raw_metric(_mean(rows, key), suffix) for _, key, _, suffix in metrics]
    rows_ui = []
    for (label, _, _, _), delta, selected_value, average_value in zip(
        metrics, deltas, selected_values, average_values, strict=True
    ):
        color = "#23a67a" if delta >= 0 else "#ff334a"
        rows_ui.append(
            _benchmark_row(
                label=label,
                delta=delta,
                selected_value=selected_value,
                average_value=average_value,
                color=color,
            )
        )

    return html.Div(className="benchmark-panel", children=rows_ui)


def _build_histogram(rows: list[dict], selected_crop: dict | None, metric: str) -> go.Figure:
    if not rows:
        return _empty_figure("No crops match the current explorer filters", height=320)

    metric = metric if metric in AXIS_LABELS else "profit_per_day"
    values = [float(row.get(metric, 0.0)) for row in rows]
    selected_value = float(selected_crop.get(metric, 0.0)) if selected_crop else None
    metric_label = AXIS_LABELS.get(metric, metric.replace("_", " ").title())

    figure = go.Figure(
        go.Histogram(
            x=values,
            nbinsx=min(12, max(4, len(rows))),
            marker={"color": "#1497ee", "line": {"color": "#ffffff", "width": 1}, "opacity": 0.78},
            hovertemplate=f"{metric_label}: %{{x:,.2f}}<br>Crops: %{{y}}<extra></extra>",
        )
    )
    if selected_value is not None:
        figure.add_vline(
            x=selected_value,
            line_color="#ff334a",
            line_dash="dot",
            line_width=2,
            annotation_text="selected",
            annotation_position="top",
        )
    figure.update_layout(
        height=320,
        bargap=0.08,
        margin={"l": 58, "r": 22, "t": 16, "b": 54},
        font={"color": "#24384a", "family": "Inter, Segoe UI, sans-serif", "size": 12},
        hoverlabel=_hover_label_style(),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=_axis_style(metric_label),
        yaxis=_axis_style("Crop Count"),
    )
    return figure


def _build_comparison_panel(rows: list[dict], selected_crop: dict | None) -> list[object]:
    if not rows or selected_crop is None:
        return [html.H3("No crop selected"), html.P("Select a crop in the scatter plot or table.")]

    averages = {
        "profit_per_day": _mean(rows, "profit_per_day"),
        "profit_total": _mean(rows, "profit_total"),
        "roi": _mean(rows, "roi"),
        "growth_days": _mean(rows, "growth_days"),
        "seed_price": _mean(rows, "seed_price"),
    }

    profit_delta = _percent_delta(float(selected_crop["profit_per_day"]), averages["profit_per_day"])
    speed_delta = _percent_delta(averages["growth_days"], float(selected_crop["growth_days"]))

    return [
        html.H3(selected_crop["crop_name"]),
        html.P(_comparison_sentence(selected_crop, profit_delta, speed_delta)),
        html.Div(
            className="metric-grid explorer-metric-grid",
            children=[
                _metric_tile("Profit/day", f"{selected_crop['profit_per_day']:,.1f}g", profit_delta),
                _metric_tile("Total profit", f"{selected_crop['profit_total']:,.0f}g", None),
                _metric_tile("ROI", f"{selected_crop['roi']:.2f}", None),
                _metric_tile("Growth", f"{selected_crop['growth_days']} days", speed_delta),
                _metric_tile("Seed price", f"{selected_crop['seed_price']:,.0f}g", None),
                _metric_tile("Harvests", f"{selected_crop['harvest_count']}", None),
            ],
        ),
    ]


def _metric_tile(label: str, value: str, delta: float | None = None) -> html.Div:
    delta_node = []
    if delta is not None:
        direction = "higher" if delta >= 0 else "lower"
        delta_node = [html.Span(f"{abs(delta):.0f}% {direction} than avg", className="metric-delta")]

    return html.Div(
        className="metric-tile",
        children=[
            html.Span(label, className="metric-label"),
            html.Strong(value, className="metric-value"),
            *delta_node,
        ],
    )


def _group_rows(rows: list[dict], color_by: str) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = _group_label(row.get(color_by), color_by)
        groups.setdefault(key, []).append(row)
    return groups


def _group_label(value: Any, color_by: str) -> str:
    if color_by == "is_regrowable":
        return "Regrowable" if value else "Single harvest"
    if color_by == "is_trellis":
        return "Trellis" if value else "Non-trellis"
    if color_by == "affordable":
        return "Affordable" if value is True else "Over budget"
    if color_by == "can_mature":
        return "Will mature" if value else "Too late"
    return str(value)


def _marker_size(row: dict) -> float:
    profit = max(0.0, float(row.get("profit_total", 0)))
    return min(34, max(10, 10 + math.sqrt(profit) / 24))


def _clicked_crop_id(click_data: dict | None) -> str | None:
    points = (click_data or {}).get("points") or []
    if not points:
        return None
    custom_data = points[0].get("customdata")
    if isinstance(custom_data, list) and custom_data:
        return str(custom_data[0])
    return None


def _selected_table_rows(rows: list[dict], selected_crop_id: str | None) -> list[int]:
    if not rows:
        return []
    for index, row in enumerate(rows):
        if row.get("crop_id") == selected_crop_id:
            return [index]
    return [0]


def _benchmark_status(rows: list[dict], selected_crop: dict | None) -> str:
    if not rows or selected_crop is None:
        return "Select a crop to compare it against the visible average."
    return f"{selected_crop['crop_name']} compared with {len(rows)} visible crops. Scores are normalized per metric."


def _comparison_sentence(selected_crop: dict, profit_delta: float, speed_delta: float) -> str:
    profit_direction = "higher" if profit_delta >= 0 else "lower"
    speed_direction = "faster" if speed_delta >= 0 else "slower"
    return (
        f"{selected_crop['crop_name']} profit/day is {abs(profit_delta):.0f}% {profit_direction} than the visible "
        f"crop average, and its first growth cycle is {abs(speed_delta):.0f}% {speed_direction} than average."
    )


def _percent_delta(value: float, baseline: float) -> float:
    if math.isclose(baseline, 0):
        return 0.0
    return ((value - baseline) / abs(baseline)) * 100


def _signed_percent_delta(rows: list[dict], row: dict, key: str, high_is_good: bool) -> float:
    average = _mean(rows, key)
    value = float(row.get(key, 0))
    if math.isclose(average, 0):
        return 0.0
    raw_delta = ((value - average) / abs(average)) * 100
    return raw_delta if high_is_good else -raw_delta


def _format_delta_label(delta: float) -> str:
    if abs(delta) < 0.5:
        return "At avg"
    return f"{delta:+.0f}%"


def _benchmark_row(label: str, delta: float, selected_value: str, average_value: str, color: str) -> html.Div:
    magnitude = min(100.0, max(2.0, abs(delta)))
    fill_class = "benchmark-fill positive" if delta >= 0 else "benchmark-fill negative"
    align_class = "benchmark-delta positive" if delta >= 0 else "benchmark-delta negative"
    return html.Div(
        className="benchmark-row",
        children=[
            html.Div(
                className="benchmark-head",
                children=[
                    html.Span(label, className="benchmark-label"),
                    html.Span(_format_delta_label(delta), className=align_class),
                ],
            ),
            html.Div(
                className="benchmark-values",
                children=[
                    html.Span(f"Selected {selected_value}", className="benchmark-selected"),
                    html.Span(f"Average {average_value}", className="benchmark-average"),
                ],
            ),
            html.Div(
                className="benchmark-track",
                children=[
                    html.Div(className="benchmark-midline"),
                    html.Div(
                        className=fill_class,
                        style={
                            "width": f"{magnitude * 0.5}%",
                            "background": color,
                            "backgroundImage": "none",
                            "backgroundRepeat": "no-repeat",
                            "boxShadow": "none",
                        },
                    ),
                ],
            ),
        ],
    )


def _format_raw_metric(value: float, suffix: str) -> str:
    if suffix == "x":
        return f"{value:.2f}x"
    if suffix:
        return f"{value:,.1f}{suffix}"
    return f"{value:,.1f}"


def _mean(rows: list[dict], key: str) -> float:
    values = [float(row.get(key, 0)) for row in rows]
    return sum(values) / len(values) if values else 0.0


def _axis_style(title: str) -> dict[str, Any]:
    return {
        "automargin": True,
        "fixedrange": True,
        "gridcolor": "#e4ebf2",
        "linecolor": "#c8d2dc",
        "showline": True,
        "tickfont": {"color": "#536679", "size": 11},
        "title": {"text": title, "standoff": 12},
        "zeroline": False,
    }


def _hover_label_style() -> dict[str, Any]:
    return {
        "bgcolor": "#143047",
        "bordercolor": "#143047",
        "font": {"color": "#ffffff", "family": "Inter, Segoe UI, sans-serif", "size": 12},
    }


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


def _to_table_row(row: dict) -> dict:
    table_row = {"crop_id": row["crop_id"]}
    for column in TABLE_COLUMNS:
        column_id = column["id"]
        table_row[column_id] = row.get(column_id)

    for key in ("seed_price", "growth_days", "harvest_count"):
        table_row[key] = int(table_row[key])
    for key in ("profit_total", "profit_per_day", "roi"):
        table_row[key] = round(float(table_row[key]), 2)
    return table_row
