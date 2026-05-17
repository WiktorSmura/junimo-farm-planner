from dash import html, register_page

register_page(__name__, path="/processing-lab", name="Processing Lab", order=4)

layout = html.Div(
    className="page-card",
    children=[
        html.P("Value add view", className="badge"),
        html.H2("Processing Lab"),
        html.P("A place to compare raw crop value against processing options such as jelly, pickles, and wine."),
    ],
)
