from dash import html, register_page

register_page(__name__, path="/", name="Plan Today", order=1)

layout = html.Div(
    [
        html.H2("Plan Today"),
        html.P("Daily farm planning dashboard."),
    ]
)
