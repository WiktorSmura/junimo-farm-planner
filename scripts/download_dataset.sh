#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Target directory
TARGET_DIR="data/raw"

# Create the target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

echo "Downloading Stardew Valley Crops dataset into $TARGET_DIR..."

# Use Kaggle CLI to download and unzip the dataset directly into data/raw
uv run kaggle datasets download -d juletopi/stardew-valley-crops-updated --path "$TARGET_DIR" --unzip

echo "Creating canonical raw dataset at $TARGET_DIR/stardew_crops_raw.csv..."
uv run python - <<'PY'
from pathlib import Path

import pandas as pd

raw_dir = Path("data/raw")
source_files = [
    raw_dir / "spring_crops_info.csv",
    raw_dir / "summer_crops_info.csv",
    raw_dir / "fall_crops_info.csv",
    raw_dir / "winter_crops_info.csv",
    raw_dir / "special_crops_info.csv",
]

frames = [pd.read_csv(path) for path in source_files if path.exists()]
if not frames:
    raise SystemExit("No raw crop source files were found.")

raw = pd.concat(frames, ignore_index=True)
raw.to_csv(raw_dir / "stardew_crops_raw.csv", index=False)
PY

echo "Download complete! Files extracted to $TARGET_DIR"
