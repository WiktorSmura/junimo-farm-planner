import dash
from dash import Dash, dcc, html, page_container

app = Dash(__name__, use_pages=True)
server = app.server

app.layout = html.Div(
    [
        html.H1("Junimo Farm Planner"),
        html.Nav([dcc.Link(page["name"], href=page["relative_path"]) for page in dash.page_registry.values()]),
        page_container,
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
