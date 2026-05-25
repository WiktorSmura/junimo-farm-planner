from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dash_table, dcc, html, register_page

from src.farm_math import compute_harvest_schedule
from src.figures import CHART_COLORS, CHART_PALETTE, axis_style, base_layout

register_page(__name__, path="/harvest-calendar", name="Harvest Calendar", order=3)

COLOR_PALETTE = CHART_PALETTE

layout = html.Div(
    className="page-card calendar-page",
    children=[
        html.Div(
            className="page-head",
            children=[
                html.P("Timing workspace", className="badge"),
                html.H2("Harvest Calendar"),
                html.P("See timing and cash-flow consequences. If planting today, when will you earn money?"),
            ],
        ),
        html.Section(
            className="plan-section",
            children=[
                html.Div(
                    className="section-head",
                    children=[
                        html.H3("Select Crops to Compare"),
                        html.P("Compare up to 3 crops (dropdown uses crops available for current season context)."),
                    ],
                ),
                dcc.Dropdown(
                    id="calendar-crop-select",
                    multi=True,
                    placeholder="Select up to 3 crops...",
                    className="control-field",
                    options=[],  # Will be populated by callback
                ),
                html.Div(id="calendar-warnings", className="warning-panel", style={"marginTop": "1rem"}),
            ],
        ),
        html.Div(
            className="calendar-main-grid",
            children=[
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Harvest Timeline"),
                                html.P("When planting and harvests occur."),
                            ],
                        ),
                        dcc.Graph(
                            id="calendar-gantt",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "300px"},
                        ),
                    ],
                ),
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Calendar Heatmap"),
                                html.P("Expected gold earned on each day of the season."),
                            ],
                        ),
                        dcc.Graph(
                            id="calendar-heatmap",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "350px"},
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className="calendar-bottom-grid",
            children=[
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Cumulative Profit"),
                                html.P("Profit over the remainder of the season."),
                            ],
                        ),
                        dcc.Graph(
                            id="calendar-profit-chart",
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "400px"},
                        ),
                    ],
                ),
                html.Section(
                    className="plan-section",
                    children=[
                        html.Div(
                            className="section-head",
                            children=[
                                html.H3("Event Schedule"),
                                html.P("Detailed interactions across the season."),
                            ],
                        ),
                        dash_table.DataTable(
                            id="calendar-event-table",
                            columns=[
                                {"name": "Crop", "id": "crop"},
                                {"name": "Event", "id": "event"},
                                {"name": "Day", "id": "day"},
                                {"name": "Revenue", "id": "revenue"},
                                {"name": "Cum. Profit", "id": "cumulative_profit"},
                            ],
                            data=[],
                            sort_action="native",
                            page_action="none",
                            fixed_rows={"headers": True},
                            style_as_list_view=True,
                            style_table={
                                "overflowX": "auto",
                                "overflowY": "auto",
                                "maxHeight": "420px",
                                "width": "100%",
                            },
                            style_cell={
                                "fontFamily": "Inter, Segoe UI, sans-serif",
                                "fontSize": 13,
                                "padding": "8px",
                            },
                            style_header={"fontFamily": "Inter, Segoe UI, sans-serif", "fontWeight": 700},
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@callback(
    Output("calendar-crop-select", "options"),
    Output("calendar-crop-select", "value"),
    Input("filtered-crops-store", "data"),
    State("calendar-crop-select", "value"),
)
def update_crop_options(filtered_data, current_selection):
    if not filtered_data:
        return [], []

    rows = filtered_data
    opts = [{"label": r["crop_name"], "value": r["crop_id"]} for r in rows]

    val = current_selection if current_selection else []

    opts_values = [o["value"] for o in opts]
    val = [v for v in val if v in opts_values]

    # Phase 9 scope: compare up to 3 crops.
    val = val[:3]

    if len(val) == 0 and rows:
        val = [rows[0]["crop_id"]]

    return opts, val


@callback(
    Output("calendar-warnings", "children"),
    Output("calendar-gantt", "figure"),
    Output("calendar-gantt", "style"),
    Output("calendar-heatmap", "figure"),
    Output("calendar-heatmap", "style"),
    Output("calendar-profit-chart", "figure"),
    Output("calendar-event-table", "data"),
    Input("calendar-crop-select", "value"),
    Input("filtered-crops-store", "data"),
    Input("day-control", "value"),
    Input("tiles-control", "value"),
)
def update_calendar_views(selected_crops, rows, current_day, tiles):
    if not rows or not selected_crops:
        return (
            html.Div(),
            go.Figure(),
            {"height": "300px"},
            go.Figure(),
            {"height": "350px"},
            go.Figure(),
            [],
        )

    # Limit to up to 3 crops
    selected_crops = selected_crops[:3]

    rows_dict = {r["crop_id"]: r for r in rows}

    events_data = []
    warnings = []

    for i, crop_id in enumerate(selected_crops):
        if crop_id not in rows_dict:
            continue
        crop = rows_dict[crop_id]

        if not crop["can_mature"]:
            warnings.append(
                html.Div(
                    f"Warning: {crop['crop_name']} will not mature before the end of the season.",
                    className="badge",
                    style={
                        "backgroundColor": "#ff334a",
                        "color": "white",
                        "marginRight": "8px",
                        "display": "inline-block",
                    },
                )
            )

        schedule = compute_harvest_schedule(
            seed_price=crop["seed_price"],
            sell_price=crop["sell_price_effective"],
            growth_days=crop["growth_days"],
            regrowth_days=crop["regrowth_days"],
            current_day=current_day,
            tiles=tiles,
            yield_per_harvest=crop.get("yield_per_harvest", crop.get("base_yield", 1.0)),
            season_length=crop["window_days"],
            special_harvest_model=(crop.get("special_harvest_model") or None),
        )

        for event in schedule:
            events_data.append(
                {
                    "crop": crop["crop_name"],
                    "crop_id": crop_id,
                    "color": COLOR_PALETTE[i % len(COLOR_PALETTE)],
                    "event": event["event"],
                    "day": event["day"],
                    "revenue": event["revenue"],
                    "cost": event["cost"],
                    "profit": event["profit"],
                    "cumulative_profit": event["cumulative_profit"],
                }
            )

    if not events_data:
        return (
            warnings,
            go.Figure(),
            {"height": "300px"},
            go.Figure(),
            {"height": "350px"},
            go.Figure(),
            [],
        )

    df_events = pd.DataFrame(events_data)

    # Multi-season crops can generate harvest events beyond day 28 within the active window.
    max_day = max(int(df_events["day"].max() if not df_events.empty else 28), 28)

    # 1. Timeline chart
    fig_gantt = go.Figure()
    shown_plant_legend = False
    shown_harvest_legend = False
    for i, crop_id in enumerate(selected_crops):
        if crop_id not in rows_dict:
            continue
        crop_name = rows_dict[crop_id]["crop_name"]
        df_c = df_events[df_events["crop_id"] == crop_id]
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]

        plants = df_c[df_c["event"] == "Plant"]["day"].tolist()
        harvests = df_c[df_c["event"] == "Harvest"]["day"].tolist()

        if plants and harvests:
            fig_gantt.add_trace(
                go.Scatter(
                    x=[min(plants), max(harvests)],
                    y=[crop_name, crop_name],
                    mode="lines",
                    line={"color": color, "width": 4},
                    opacity=0.38,
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        fig_gantt.add_trace(
            go.Scatter(
                x=plants,
                y=[crop_name] * len(plants),
                mode="markers",
                marker={
                    "symbol": "triangle-right",
                    "size": 13,
                    "color": color,
                    "line": {"color": CHART_COLORS["cream"], "width": 1},
                },
                name="Plant",
                legendgroup="Plant",
                showlegend=not shown_plant_legend,
                customdata=[[crop_name] for _ in plants],
                hovertemplate="<b>%{customdata[0]}</b><br>Plant on day %{x}<extra></extra>",
            )
        )
        shown_plant_legend = True

        fig_gantt.add_trace(
            go.Scatter(
                x=harvests,
                y=[crop_name] * len(harvests),
                mode="markers",
                marker={
                    "symbol": "star",
                    "size": 14,
                    "color": CHART_COLORS["gold"],
                    "line": {"color": color, "width": 2},
                },
                name="Harvest",
                legendgroup="Harvest",
                showlegend=not shown_harvest_legend,
                customdata=[[crop_name] for _ in harvests],
                hovertemplate="<b>%{customdata[0]}</b><br>Harvest on day %{x}<extra></extra>",
            )
        )
        shown_harvest_legend = True

    gantt_height = max(300, 120 + (len(selected_crops) * 60))
    fig_gantt.update_layout(
        **base_layout(height=gantt_height, margin={"l": 118, "r": 26, "t": 34, "b": 48}),
        xaxis={**axis_style("Day"), "range": [1, max_day], "dtick": max(1, max_day // 14)},
        yaxis={"fixedrange": True, "title": "", "tickfont": {"color": CHART_COLORS["ink"], "size": 12}},
        showlegend=True,
        legend={"orientation": "h", "x": 0, "y": 1.12},
    )
    if max_day > 28:
        fig_gantt.add_vline(
            x=28,
            line_color=CHART_COLORS["brown"],
            line_dash="dot",
            line_width=1,
            annotation_text="season end",
            annotation_position="top",
            annotation_font={"size": 10, "color": CHART_COLORS["muted"]},
        )

    # 2. Cumulative Profit Chart (Line chart with step)
    fig_profit = go.Figure()

    for i, crop_id in enumerate(selected_crops):
        if crop_id not in rows_dict:
            continue
        crop_name = rows_dict[crop_id]["crop_name"]
        df_c = df_events[df_events["crop_id"] == crop_id].sort_values("day")

        if df_c.empty:
            continue

        # Ensure it starts at 0 at current_day
        x_vals = [current_day] + df_c["day"].tolist()
        y_vals = [0.0] + df_c["cumulative_profit"].tolist()

        fig_profit.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines+markers",
                line_shape="vh",  # step chart
                name=crop_name,
                line={"color": COLOR_PALETTE[i % len(COLOR_PALETTE)], "width": 3},
                marker={"size": 8, "line": {"color": CHART_COLORS["cream"], "width": 1}},
                hovertemplate="<b>%{fullData.name}</b><br>Day %{x}<br>Cumulative profit: %{y:,.0f}g<extra></extra>",
            )
        )

    fig_profit.update_layout(
        **base_layout(height=400, margin={"l": 72, "r": 30, "t": 24, "b": 52}),
        legend={"orientation": "h", "x": 0, "y": 1.12},
        xaxis={**axis_style("Day"), "range": [1, max_day], "dtick": max(1, max_day // 14)},
        yaxis=axis_style("Cumulative Profit", ticksuffix="g"),
    )
    fig_profit.add_hline(y=0, line_color=CHART_COLORS["brown"], line_dash="dot", line_width=1, opacity=0.6)

    # 3. Calendar Heatmap
    # Group by revenue per day
    df_rev = df_events[df_events["event"] == "Harvest"].groupby("day")["revenue"].sum().reset_index()

    weeks = math.ceil(max_day / 7)

    # Make a grid for generated weeks (rows of 7 days)
    # We will compute total revenue for all selected crops per day.
    heatmap_z = []
    text_z = []
    custom_z = []

    for week in range(weeks):
        week_z = []
        week_text = []
        week_custom = []
        for d in range(1, 8):
            day_num = week * 7 + d
            val_rows = df_rev[df_rev["day"] == day_num]
            val = val_rows["revenue"].iloc[0] if not val_rows.empty else 0
            week_z.append(val)
            week_text.append(f"{day_num}<br>{val:,.0f}g" if val > 0 else f"{day_num}")
            week_custom.append([day_num, val])
        heatmap_z.append(week_z)
        text_z.append(week_text)
        custom_z.append(week_custom)

    # Reverse to start from top
    heatmap_z = heatmap_z[::-1]
    text_z = text_z[::-1]
    custom_z = custom_z[::-1]

    y_labels = [f"Week {i}" for i in range(weeks, 0, -1)]

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=heatmap_z,
            x=["1", "2", "3", "4", "5", "6", "7"],
            y=y_labels,
            text=text_z,
            customdata=custom_z,
            texttemplate="%{text}",
            colorscale=[[0, "#fff6dc"], [0.45, "#dce8bd"], [1, CHART_COLORS["green"]]],
            showscale=True,
            hovertemplate="Day %{customdata[0]}<br>Revenue: %{customdata[1]:,.0f}g<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )

    heatmap_height = max(350, 120 + weeks * 48)
    fig_heatmap.update_layout(
        **base_layout(height=heatmap_height, margin={"l": 58, "r": 24, "t": 18, "b": 42}),
        xaxis={"title": "Day in Week", "fixedrange": True, "side": "top"},
        yaxis={"title": "", "fixedrange": True},
    )

    # Format event table
    table_data = []
    for _, row in df_events.sort_values(by=["day", "event"], ascending=[True, False]).iterrows():
        table_data.append(
            {
                "crop": row["crop"],
                "event": row["event"],
                "day": row["day"],
                "revenue": f"{row['revenue']:,.0f}g",
                "cumulative_profit": f"{row['cumulative_profit']:,.0f}g",
            }
        )

    return (
        warnings,
        fig_gantt,
        {"height": f"{gantt_height}px"},
        fig_heatmap,
        {"height": f"{heatmap_height}px"},
        fig_profit,
        table_data,
    )
