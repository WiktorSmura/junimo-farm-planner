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
        html.H3("Calculation assumptions"),
        html.Ul(
            [
                html.Li("Days left formula: 28 - current day + 1."),
                html.Li("Non-regrowing crops are replanted after each harvest."),
                html.Li("Regrowing crops pay seed cost once per tile."),
                html.Li("Profit = revenue - seed cost, ROI = profit / seed cost."),
                html.Li("Fertilizer control uses approximate growth-speed factors for planning."),
                html.Li("Processing mode uses planning multipliers until full processing simulation is added."),
            ]
        ),
    ],
)
