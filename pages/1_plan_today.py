from dash import html, register_page

register_page(__name__, path="/", name="Plan Today", order=1)

layout = html.Div(
    className="page-card",
    children=[
        html.P("Phase 1-3 foundation", className="badge"),
        html.H2("Plan Today"),
        html.P(
            "This page will become the quick decision screen for choosing crops based on season, day, budget, and farm space."
        ),
        html.Ul(
            [
                html.Li("Recommended crops ranked by baseline profitability."),
                html.Li("A compact explanation of why each crop is recommended."),
                html.Li("A linked crop selection that drives the rest of the dashboard."),
            ]
        ),
    ],
)
