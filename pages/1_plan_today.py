from __future__ import annotations

from dash import Input, Output, callback, html, register_page

register_page(__name__, path="/", name="Plan Today", order=1)

layout = html.Div(
    className="page-card",
    children=[
        html.P("Daily decision view", className="badge"),
        html.H2("Plan Today"),
        html.P(
            "Use the global controls above to rank crops for the current season and day. "
            "This page focuses on a fast planting decision."
        ),
        html.Div(id="plan-today-content", className="plan-grid"),
    ],
)


@callback(
    Output("plan-today-content", "children"),
    Input("filtered-crops-store", "data"),
    Input("selected-crop-store", "data"),
)
def render_plan_today(filtered_rows: list[dict] | None, selected_crop: dict | None):
    rows = filtered_rows or []
    if not rows:
        return [
            html.Div(
                className="detail-card",
                children=[
                    html.H3("No crops match"),
                    html.P("Try lowering day, increasing tiles, changing season, or clearing search text to see options."),
                ],
            )
        ]

    top_rows = rows[:8]
    table = html.Table(
        className="plan-table",
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th("Crop"),
                        html.Th("Profit"),
                        html.Th("Profit/day"),
                        html.Th("Harvests"),
                        html.Th("Cost"),
                        html.Th("Warnings"),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(row["crop_name"]),
                            html.Td(f"{row['profit_total']:.0f}g"),
                            html.Td(f"{row['profit_per_day']:.1f}g"),
                            html.Td(str(row["harvest_count"])),
                            html.Td(f"{row['seed_cost']:.0f}g"),
                            html.Td(
                                html.Div(
                                    className="warning-flags",
                                    children=[
                                        html.Span(flag, className="warning-flag")
                                        for flag in (row["warning_flags"] or ["Clear"])
                                    ],
                                )
                            ),
                        ]
                    )
                    for row in top_rows
                ]
            ),
        ],
    )

    details = _selected_crop_details(selected_crop or rows[0])
    return [table, details]


def _selected_crop_details(crop: dict) -> html.Div:
    return html.Div(
        className="detail-card",
        children=[
            html.H3(crop["crop_name"]),
            html.Ul(
                className="detail-list",
                children=[
                    html.Li(f"Expected profit: {crop['profit_total']:.0f}g"),
                    html.Li(f"Profit per day: {crop['profit_per_day']:.1f}g"),
                    html.Li(f"Seed cost: {crop['seed_cost']:.0f}g"),
                    html.Li(f"Expected harvests: {crop['harvest_count']}"),
                    html.Li(f"First harvest day: {crop['first_harvest_day']}"),
                    html.Li(f"Window days available: {crop['window_days']}"),
                    html.Li(f"ROI: {crop['roi']:.2f}"),
                ],
            ),
            html.P(crop.get("rule_note") or "No special restrictions noted for this crop."),
        ],
    )
