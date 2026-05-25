from dash import html, register_page

register_page(__name__, path="/about", name="About", order=6)

layout = html.Div(
    className="page-card about-page",
    children=[
        html.Div(
            className="page-head",
            children=[
                html.P("Project notes", className="badge"),
                html.H2("About / Help"),
                html.P(
                    "Junimo Farm Planner helps Stardew Valley players decide what to plant based on season, "
                    "current day, budget, farm space, and profit strategy."
                ),
            ],
        ),
        html.Section(
            className="plan-section detail-card",
            children=[
                html.H3("How to use it"),
                html.Ol(
                    [
                        html.Li("Choose the current season in the global Farm Context panel."),
                        html.Li("Set the current day, farm tiles, budget, goal, fertilizer, and optional crop search."),
                        html.Li("Use Plan Today for the fastest recommendation."),
                        html.Li("Click a crop row or chart point to update crop details across linked pages."),
                        html.Li("Open Harvest Calendar to inspect timing and cash flow."),
                        html.Li("Open Processing Lab to compare raw sale value against processing options."),
                        html.Li("Open Farm Mix to generate a concrete planting allocation under budget and tile limits."),
                    ]
                ),
            ],
        ),
        html.Section(
            className="plan-section detail-card",
            children=[
                html.H3("Data sources"),
                html.P(
                    "The app uses the Stardew Valley Crops Updated Kaggle dataset, stored as immutable raw CSV "
                    "files under data/raw and transformed into data/processed/crops_clean.csv. Additional game-rule "
                    "metadata, including trellis flags, yields, processing categories, and crop availability notes, "
                    "is curated in src/constants.py."
                ),
            ],
        ),
        html.Section(
            className="plan-section detail-card",
            children=[
                html.H3("Formula explanation"),
                html.Ul(
                    [
                        html.Li("Days left = 28 - current day + 1."),
                        html.Li("A crop planted on day D with N growth days is harvested on day D + N."),
                        html.Li("Non-regrowing crops are replanted immediately after each harvest."),
                        html.Li("Regrowing crops pay seed cost once per tile and then follow their regrowth interval."),
                        html.Li("Revenue = harvest count x sell price x expected yield x planted tiles."),
                        html.Li("Profit = revenue - seed cost."),
                        html.Li("ROI = profit / seed cost, with zero seed cost treated as 0 ROI for ranking safety."),
                        html.Li("Profit per day = profit / remaining planting window."),
                        html.Li("Affordability compares total seed cost against the current budget."),
                        html.Li("Maturity checks whether at least one harvest fits inside the active season window."),
                    ]
                ),
            ],
        ),
        html.Section(
            className="plan-section detail-card",
            children=[
                html.H3("Processing assumptions"),
                html.Ul(
                    [
                        html.Li("Kegs, Preserves Jars, Mills, and Oil Makers use curated Stardew formulas."),
                        html.Li("Processing throughput is estimated from machine count and horizon days."),
                        html.Li("Leftover produce is assumed to be sold raw."),
                        html.Li("The model does not simulate exact harvest-day inventory queues."),
                    ]
                ),
            ],
        ),
        html.Section(
            className="plan-section detail-card",
            children=[
                html.H3("Limitations"),
                html.Ul(
                    [
                        html.Li(
                            "Crop quality, professions other than the Processing Lab artisan toggle, and cask aging are "
                            "simplified."
                        ),
                        html.Li("Fertilizer growth effects are approximate planning factors."),
                        html.Li("Rare random extra yields are mostly excluded unless a stable expectation is documented."),
                        html.Li(
                            "Greenhouse, Ginger Island, Garden Pot, and quest-only contexts are documented but not "
                            "fully simulated."
                        ),
                        html.Li("Farm Mix uses a greedy allocation algorithm rather than a full integer optimization solver."),
                    ]
                ),
            ],
        ),
        html.Section(
            className="plan-section detail-card",
            children=[
                html.H3("Credits"),
                html.P(
                    "Stardew Valley is created by ConcernedApe. This fan-made dashboard is for planning and coursework use."
                ),
            ],
        ),
    ],
)
