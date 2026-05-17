# Data Directory

This directory contains the data used for the Junimo Farm Planner.

## Structure

- `raw/`: Contains originally downloaded, immutable data. Treat this as read-only.
- `processed/`: Contains cleaned and transformed data generated from the raw data, ready to be used by the application.

## Downloading the Dataset

The application relies on the [Stardew Valley Crops Updated](https://www.kaggle.com/datasets/juletopi/stardew-valley-crops-updated) dataset from Kaggle.

### Prerequisites

1. Ensure the Kaggle CLI is installed (e.g., via `pip install kaggle`).
2. Generate an API token from your Kaggle account settings.
3. Place the downloaded `kaggle.json` file in `~/.kaggle/kaggle.json` and restrict its permissions:
   ```bash
   mkdir -p ~/.kaggle
   chmod 600 ~/.kaggle/kaggle.json
   ```

### Instructions

To automatically download and extract the dataset into the `raw/` directory, run the provided helper script from the root of the project:

```bash
chmod +x scripts/download_dataset.sh
./scripts/download_dataset.sh
```

## Processing the Data

After the raw CSVs are in `data/raw/`, build the cleaned dataset with the loader:

```bash
uv run python - <<'PY'
from src.data_loader import load_clean_crops

load_clean_crops(force_refresh=True)
PY
```

This reads the raw crop files, applies the game-rule corrections, and writes `data/processed/crops_clean.csv`.

## Data Dictionary

### Raw data

| File | Purpose |
| --- | --- |
| `raw/stardew_crops_raw.csv` | Canonical raw crop dataset used by the loader |
| `raw/*_crops_info.csv` | Season-specific source files retained for traceability |
| `processed/crops_clean.csv` | Cleaned dataset generated from the raw files |

### Clean data

| Column | Type | Meaning |
| --- | --- | --- |
| `crop_id` | string | Stable slug used for row selection |
| `crop_name` | string | Normalized crop name |
| `season` | string | Season label for display, such as `Spring` or `Spring/Summer` |
| `seasons_list` | list[string] | Parsed list of supported seasons |
| `seed_price` | integer | Seed cost in gold |
| `sell_price_raw` | integer | Base sell price before quality or processing |
| `growth_days` | integer | Days from planting to first harvest |
| `regrowth_days` | integer | Days between subsequent harvests for regrowable crops |
| `is_regrowable` | boolean | `True` when the crop can produce multiple harvests |
| `is_trellis` | boolean | `True` for known trellis crops in the dataset |
| `is_multi_season` | boolean | `True` when the crop is available in more than one season |
| `is_quest_only` | boolean | `True` for quest-limited crops such as Qi Fruit |
| `rule_note` | string | Applied game-rule note for season/location or availability constraints |
| `available_days` | integer | Baseline contiguous planting window in days for Valley seasons |
| `base_yield` | integer | Deterministic items per harvest (e.g., Blueberry `3`, Coffee Bean `4`) |
| `max_harvests` | integer | Baseline max harvest count across the contiguous season window |
| `profit_total` | integer | Baseline raw profit over the contiguous season window |
| `profit_per_day` | float | Baseline profit normalized by `available_days` |
| `roi` | float | Baseline return on seed cost |
| `affordable` | boolean or null | Reserved for budget-aware planning inputs |
| `will_mature` | boolean or null | Reserved for day-sensitive planning inputs |
| `first_harvest_day` | integer or null | Baseline first harvest day from planting (`growth_days + 1`) |

## Missing or unclear fields

- `trellis` is not present in the source dataset and must be curated manually
- `crop_type` is not present in the source dataset
- probabilistic extra-yield behavior is not modeled in baseline calculations
- processing values are not present in the source dataset
- `affordable`, `will_mature`, and `first_harvest_day` will later depend on user inputs
