import dash
from dash import Dash, Input, Output, callback, dcc, html, page_container

from src.dashboard_state import (
    DEFAULT_FILTERS,
    FERTILIZER_OPTIONS,
    PROCESSING_OPTIONS,
    SEASON_OPTIONS,
    build_filtered_snapshot,
)

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="Junimo Farm Planner",
    update_title="Loading...",
)
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""
server = app.server


def _page_links() -> list[html.A]:
    pages = sorted(dash.page_registry.values(), key=lambda page: page.get("order", 0))
    return [dcc.Link(page["name"], href=page["relative_path"], className="nav-link") for page in pages]


def _control_field(title: str, body: object, hint: str) -> html.Div:
    return html.Div(
        className="control-field",
        children=[
            html.Label(title, className="control-label"),
            body,
            html.P(hint, className="control-hint"),
        ],
    )


app.layout = html.Div(
    className="app-shell",
    children=[
        html.Header(
            className="app-header",
            children=[
                html.Div(
                    className="brand-lockup",
                    children=[
                        html.Img(src="/assets/logo.svg", alt="Junimo Farm Planner logo", className="app-logo"),
                        html.Div(
                            children=[
                                html.P("Stardew Valley crop planning", className="eyebrow"),
                                html.H1("Junimo Farm Planner"),
                                html.P(
                                    "Planting decisions for the current season, budget, and farm capacity.",
                                    className="app-tagline",
                                ),
                            ]
                        ),
                    ],
                ),
                html.Nav(className="app-nav desktop-nav", children=_page_links()),
            ],
        ),
        html.Details(
            className="mobile-nav",
            children=[
                html.Summary("Pages"),
                html.Nav(className="mobile-nav-links", children=_page_links()),
            ],
        ),
        html.Div(
            className="dashboard-layout",
            children=[
                html.Aside(
                    className="control-panel",
                    children=[
                        html.Details(
                            className="control-details",
                            children=[
                                html.Summary(
                                    className="control-panel-header",
                                    children=[
                                        html.H2("Farm Context"),
                                        html.P("Season, timing, budget, processing, and crop search."),
                                    ],
                                ),
                                html.Div(
                                    className="control-grid",
                                    children=[
                                        _control_field(
                                            "Season",
                                            dcc.Dropdown(
                                                id="season-control",
                                                options=SEASON_OPTIONS,
                                                value=DEFAULT_FILTERS["season"],
                                                clearable=False,
                                            ),
                                            "Current outdoor season",
                                        ),
                                        _control_field(
                                            "Current day",
                                            dcc.Slider(
                                                id="day-control",
                                                min=1,
                                                max=28,
                                                step=1,
                                                marks={1: "1", 7: "7", 14: "14", 21: "21", 28: "28"},
                                                value=DEFAULT_FILTERS["current_day"],
                                            ),
                                            "Remaining window in season",
                                        ),
                                        _control_field(
                                            "Farm tiles",
                                            dcc.Input(
                                                id="tiles-control",
                                                type="number",
                                                min=0,
                                                step=1,
                                                value=DEFAULT_FILTERS["tiles"],
                                                className="control-input",
                                            ),
                                            "Planting capacity",
                                        ),
                                        _control_field(
                                            "Budget (g)",
                                            dcc.Input(
                                                id="budget-control",
                                                type="number",
                                                min=0,
                                                step=100,
                                                value=DEFAULT_FILTERS["budget"],
                                                className="control-input",
                                            ),
                                            "Gold for seeds",
                                        ),
                                        _control_field(
                                            "Processing mode",
                                            dcc.Dropdown(
                                                id="processing-control",
                                                options=PROCESSING_OPTIONS,
                                                value=DEFAULT_FILTERS["processing_mode"],
                                                clearable=False,
                                            ),
                                            "Value uplift profile",
                                        ),
                                        _control_field(
                                            "Fertilizer",
                                            dcc.Dropdown(
                                                id="fertilizer-control",
                                                options=FERTILIZER_OPTIONS,
                                                value=DEFAULT_FILTERS["fertilizer"],
                                                clearable=False,
                                            ),
                                            "Growth-speed profile",
                                        ),
                                        _control_field(
                                            "Search crop",
                                            dcc.Input(
                                                id="crop-search-control",
                                                type="text",
                                                value=DEFAULT_FILTERS["search_term"],
                                                placeholder="Search crop",
                                                className="control-input",
                                            ),
                                            "Filters all crop views",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-status",
                            children=[
                                html.Div(
                                    className="control-status-heading",
                                    children=[
                                        html.H3("Current Recommendation"),
                                        html.P("Updates from the active filters."),
                                    ],
                                ),
                                html.Div(id="global-summary", className="control-summary"),
                            ],
                        ),
                    ],
                ),
                html.Main(className="page-container", children=page_container),
            ],
        ),
        dcc.Store(id="filtered-crops-store"),
        dcc.Store(id="selected-crop-store"),
    ],
)


@callback(
    Output("filtered-crops-store", "data"),
    Output("selected-crop-store", "data"),
    Output("global-summary", "children"),
    Input("season-control", "value"),
    Input("day-control", "value"),
    Input("tiles-control", "value"),
    Input("budget-control", "value"),
    Input("processing-control", "value"),
    Input("fertilizer-control", "value"),
    Input("crop-search-control", "value"),
)
def sync_shared_state(
    season: str,
    day: int,
    tiles: int,
    budget: float | None,
    processing_mode: str,
    fertilizer: str,
    search_term: str,
):
    snapshot = build_filtered_snapshot(
        season=season,
        current_day=day,
        tiles=tiles,
        budget=budget,
        goal=None,
        processing_mode=processing_mode,
        fertilizer=fertilizer,
        search_term=search_term,
    )

    summary_nodes = [html.P(snapshot["summary"], className="control-summary-text")]
    if snapshot["selected_crop"] is not None:
        selected = snapshot["selected_crop"]
        summary_nodes.append(
            html.Div(
                className="summary-pills",
                children=[
                    html.Span("Top Pick", className="summary-pill-title"),
                    html.Span(selected["crop_name"], className="summary-pill"),
                    html.Span(f"{selected['harvest_count']} harvests", className="summary-pill"),
                    html.Span(f"{selected['seed_cost']:.0f}g seed cost", className="summary-pill"),
                ],
            )
        )

    return snapshot["rows"], snapshot["selected_crop"], summary_nodes


if __name__ == "__main__":
    app.run(debug=True)
