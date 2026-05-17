from dash import html, register_page

register_page(__name__, path="/farm-mix", name="Farm Mix", order=5)

layout = html.Div(
    className="page-card",
    children=[
        html.P("Budget and space", className="badge"),
        html.H2("Farm Mix"),
        html.P("A mixed-planting planning view for fitting the right crops into a budget and tile count."),
    ],
)
