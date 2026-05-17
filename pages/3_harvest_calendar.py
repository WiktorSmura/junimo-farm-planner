from dash import html, register_page

register_page(__name__, path="/harvest-calendar", name="Harvest Calendar", order=3)

layout = html.Div(
    className="page-card",
    children=[
        html.P("Timeline view", className="badge"),
        html.H2("Harvest Calendar"),
        html.P("A harvest timeline for checking first harvest, regrowth cadence, and season fit."),
    ],
)
