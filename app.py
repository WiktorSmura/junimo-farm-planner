import dash
from dash import Dash, dcc, html, page_container

app = Dash(__name__, use_pages=True, title="Junimo Farm Planner", update_title="Loading...")
server = app.server


def _page_links() -> list[html.A]:
    pages = sorted(dash.page_registry.values(), key=lambda page: page.get("order", 0))
    return [dcc.Link(page["name"], href=page["relative_path"], className="nav-link") for page in pages]


app.layout = html.Div(
    className="app-shell",
    children=[
        html.Header(
            className="app-header",
            children=[
                html.Img(src="/assets/logo.svg", alt="Junimo Farm Planner logo", className="app-logo"),
                html.Div(
                    children=[
                        html.P("Stardew Valley crop planning", className="eyebrow"),
                        html.H1("Junimo Farm Planner"),
                        html.P(
                            "Plan what to plant today, compare crops, and understand the tradeoffs before you spend gold.",
                            className="app-tagline",
                        ),
                    ]
                ),
            ],
        ),
        html.Nav(className="app-nav", children=_page_links()),
        html.Main(className="page-container", children=page_container),
    ],
)

if __name__ == "__main__":
    app.run(debug=True)
