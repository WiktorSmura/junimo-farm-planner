# Junimo Farm Planner

Dash dashboard for Stardew Valley crop planning.

## Purpose

Help players answer one question quickly: what should I plant today?

## Run locally

```bash
uv sync
uv run python app.py
```

## Data

- Data layout, download steps, and the processing pipeline are documented in [`data/README.md`](./data/README.md)
- Raw source data lives in [`data/raw/stardew_crops_raw.csv`](./data/raw/stardew_crops_raw.csv)
- The cleaned dataset is generated at [`data/processed/crops_clean.csv`](./data/processed/crops_clean.csv)

## Project notes

Detailed planning and scope notes are stored in [`specification/phase_1_3_notes.md`](./specification/phase_1_3_notes.md).
