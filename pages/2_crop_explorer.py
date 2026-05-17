from dash import html, register_page

register_page(__name__, path="/crop-explorer", name="Crop Explorer", order=2)

layout = html.Div(
    className="page-card",
    children=[
        html.P("Browse and compare", className="badge"),
        html.H2("Crop Explorer"),
        html.P("A comparison view for reviewing the full crop catalog and understanding baseline economics."),
    ],
)
