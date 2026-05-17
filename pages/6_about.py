from dash import html, register_page

register_page(__name__, path="/about", name="About", order=6)

layout = html.Div(
    className="page-card",
    children=[
        html.P("Project notes", className="badge"),
        html.H2("About"),
        html.P(
            "This app uses a cleaned Stardew Valley crop dataset and a progressive "
            "Dash Pages structure that will expand into a decision-support dashboard."
        ),
    ],
)
