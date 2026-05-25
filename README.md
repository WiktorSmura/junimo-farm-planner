# Junimo Farm Planner

Interactive Dash dashboard for Stardew Valley crop planning.

## Description

Junimo Farm Planner helps players answer one question quickly: **what should I plant today?** It combines season, current day, farm tiles, budget, fertilizer assumptions, and strategy into crop recommendations, timing views, processing comparisons, and a farm mix plan.

## User Story

As a casual Stardew Valley player, I want to enter my current season, day, farm size, and budget so that I can quickly decide which crops to plant, compare alternatives, and understand when I will earn money back.

## Features

- Multipage Dash app using Dash Pages
- Global farm context controls and shared crop selection
- Plan Today recommendations with linked table/chart selection
- Crop Explorer scatter plot, histogram, benchmark panel, and filtered table
- Harvest Calendar timeline, heatmap, cumulative profit chart, and event table
- Processing Lab for raw sale versus machine processing estimates
- Farm Mix optimizer with strategy selector, crop exclusions, treemap, budget allocation chart, and planting table
- Custom CSS theme and visible logo
- About/help page with assumptions and limitations

## Data Sources

- Source dataset: [Stardew Valley Crops Updated](https://www.kaggle.com/datasets/juletopi/stardew-valley-crops-updated)
- Raw source data lives in [`data/raw/stardew_crops_raw.csv`](./data/raw/stardew_crops_raw.csv)
- The cleaned dataset is generated at [`data/processed/crops_clean.csv`](./data/processed/crops_clean.csv)
- Data layout, download steps, processing rules, and missing-field notes are documented in [`data/README.md`](./data/README.md)

## Dashboard Pages

- **Plan Today**: top crop recommendations, leaderboard, crop table, selected detail, budget usage, warnings, and harvest preview.
- **Crop Explorer**: visual crop trade-offs with axis controls, color controls, affordability filter, histogram, and comparison panel.
- **Harvest Calendar**: harvest timing, expected cash-flow days, cumulative profit, and event schedule for up to three crops.
- **Processing Lab**: raw versus processed value with equipment limits and throughput estimates.
- **Farm Mix**: greedy planting allocation under budget and tile constraints.
- **About**: usage notes, formulas, assumptions, limitations, and credits.

## How to Run Locally

```bash
uv sync
uv run python app.py
```

Alternative with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Formula Assumptions

- Days left: `28 - current_day + 1`
- Non-regrowing crops are replanted after each harvest
- Regrowing crops pay seed cost once per tile
- Profit: `revenue - seed_cost`
- ROI: `profit / seed_cost`
- Profit per day: `profit / remaining planting window`
- Affordability compares seed cost to budget
- Maturity checks whether at least one harvest fits before the end of the active season window

## Limitations

- Crop quality, casks, exact inventory queues, cooking, and seed maker paths are out of scope
- Fertilizer effects are approximate
- Rare random extra yields are simplified unless explicitly modeled
- Farm Mix uses a greedy allocation algorithm, not a full optimizer
- Greenhouse, Ginger Island, and quest-only crops are noted but not fully simulated as separate farm contexts

## Project Notes

Detailed planning and scope notes are stored in [`specification/phase_1_3_notes.md`](./specification/phase_1_3_notes.md).
