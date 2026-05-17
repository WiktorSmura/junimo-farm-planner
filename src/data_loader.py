from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .constants import (
    BASE_YIELD_OVERRIDES,
    CLEAN_CROPS_FILE,
    CROP_RULE_OVERRIDES,
    RAW_CROP_SOURCE_FILES,
    RAW_CROPS_FILE,
    RAW_DATA_DIR,
    SEASON_LENGTH_DAYS,
    SEASON_ORDER,
    TRELLIS_CROPS,
)

REQUIRED_RAW_COLUMNS = (
    "crop_name",
    "description",
    "days_to_grow",
    "regrowth",
    "seed_price",
    "sell_price",
    "multiple_harvests",
    "edible",
    "season",
)

OUTPUT_COLUMNS = (
    "crop_id",
    "crop_name",
    "season",
    "seasons_list",
    "description",
    "seed_price",
    "sell_price_raw",
    "growth_days",
    "regrowth_days",
    "is_regrowable",
    "is_trellis",
    "is_multi_season",
    "is_quest_only",
    "rule_note",
    "available_days",
    "base_yield",
    "max_harvests",
    "profit_total",
    "profit_per_day",
    "roi",
    "affordable",
    "will_mature",
    "first_harvest_day",
)


def load_raw_crops(raw_dir: Path | str | None = None) -> pd.DataFrame:
    raw_dir = Path(raw_dir) if raw_dir is not None else RAW_DATA_DIR
    canonical_file = raw_dir / RAW_CROPS_FILE.name

    if canonical_file.exists():
        return pd.read_csv(canonical_file)

    source_files = [raw_dir / name for name in RAW_CROP_SOURCE_FILES if (raw_dir / name).exists()]
    if not source_files:
        if canonical_file.exists():
            return pd.read_csv(canonical_file)
        raise FileNotFoundError(f"No raw crop files found in {raw_dir}")

    frames = [pd.read_csv(path) for path in source_files]
    return pd.concat(frames, ignore_index=True)


def clean_crops(df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_RAW_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required raw columns: {', '.join(missing)}")

    cleaned = df.copy()
    cleaned = cleaned[list(REQUIRED_RAW_COLUMNS)].copy()

    cleaned["crop_name"] = cleaned["crop_name"].astype(str).str.strip()
    cleaned["description"] = cleaned["description"].astype(str).str.strip()
    cleaned["season"] = cleaned["season"].astype(str).str.strip()

    for column in ("days_to_grow", "regrowth", "seed_price", "sell_price"):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce").astype("Int64")

    cleaned["multiple_harvests"] = cleaned["multiple_harvests"].map(_parse_yes_no)
    cleaned["edible"] = cleaned["edible"].map(_parse_yes_no)

    grouped_rows = []
    for crop_name, group in cleaned.groupby("crop_name", sort=True):
        seasons = _merge_seasons(group["season"].tolist())
        seasons = _apply_season_override(crop_name, seasons)
        season_label = _season_label(seasons)
        rule_override = CROP_RULE_OVERRIDES.get(crop_name, {})
        growth_days = int(group["days_to_grow"].iloc[0])
        regrowth_days = int(group["regrowth"].iloc[0])
        seed_price = int(group["seed_price"].iloc[0])
        sell_price_raw = int(group["sell_price"].iloc[0])
        is_regrowable = bool(regrowth_days > 0 or group["multiple_harvests"].fillna(False).any())
        is_trellis = crop_name in TRELLIS_CROPS
        available_days = _max_contiguous_window_days(seasons)
        base_yield = int(BASE_YIELD_OVERRIDES.get(crop_name, 1))
        first_harvest_day = growth_days + 1
        will_mature = first_harvest_day <= available_days
        max_harvests = _max_harvests(
            crop_name=crop_name,
            growth_days=growth_days,
            regrowth_days=regrowth_days,
            available_days=available_days,
            seasons_count=len(seasons),
            special_harvest_model=rule_override.get("special_harvest_model"),
        )
        profit_total = (max_harvests * sell_price_raw * base_yield) - seed_price
        profit_per_day = profit_total / available_days
        roi = None if seed_price == 0 else profit_total / seed_price
        affordable = pd.NA

        grouped_rows.append(
            {
                "crop_id": _slugify(crop_name),
                "crop_name": crop_name,
                "season": season_label,
                "seasons_list": seasons,
                "description": group["description"].iloc[0],
                "seed_price": seed_price,
                "sell_price_raw": sell_price_raw,
                "growth_days": growth_days,
                "regrowth_days": regrowth_days,
                "is_regrowable": is_regrowable,
                "is_trellis": is_trellis,
                "is_multi_season": len(seasons) > 1,
                "is_quest_only": bool(rule_override.get("quest_only", False)),
                "rule_note": rule_override.get("rule_note", ""),
                "available_days": available_days,
                "base_yield": base_yield,
                "max_harvests": max_harvests,
                "profit_total": profit_total,
                "profit_per_day": profit_per_day,
                "roi": roi,
                "affordable": affordable,
                "will_mature": will_mature,
                "first_harvest_day": first_harvest_day,
            }
        )

    result = pd.DataFrame(grouped_rows)
    result = result.loc[:, OUTPUT_COLUMNS]
    result = result.sort_values(["season", "crop_name"], kind="stable").reset_index(drop=True)
    return result


def load_clean_crops(force_refresh: bool = False) -> pd.DataFrame:
    if not force_refresh and CLEAN_CROPS_FILE.exists():
        return _read_clean_crops(CLEAN_CROPS_FILE)

    raw = load_raw_crops()
    clean = clean_crops(raw)
    save_clean_crops(clean)
    return clean


def save_clean_crops(df: pd.DataFrame, path: Path | str | None = None) -> Path:
    target = Path(path) if path is not None else CLEAN_CROPS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    serialised = df.copy()
    serialised["seasons_list"] = serialised["seasons_list"].map(_serialise_seasons_list)
    serialised.to_csv(target, index=False)
    return target


def _read_clean_crops(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "seasons_list" in df.columns:
        df["seasons_list"] = df["seasons_list"].map(_parse_seasons_list)
    return df


def _parse_yes_no(value: object) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().upper() == "YES"


def _merge_seasons(seasons: list[object]) -> list[str]:
    unique_seasons = []
    for season in seasons:
        normalized = str(season).strip()
        if normalized == "Any":
            return list(SEASON_ORDER)
        if normalized not in unique_seasons:
            unique_seasons.append(normalized)

    ordered = [season for season in SEASON_ORDER if season in unique_seasons]
    extras = [season for season in unique_seasons if season not in SEASON_ORDER]
    return ordered + extras


def _season_label(seasons: list[str]) -> str:
    if len(seasons) == len(SEASON_ORDER) and all(season in seasons for season in SEASON_ORDER):
        return "Any"
    if len(seasons) == 1:
        return seasons[0]
    return "/".join(seasons)


def _max_harvests(
    crop_name: str,
    growth_days: int,
    regrowth_days: int,
    available_days: int,
    seasons_count: int,
    special_harvest_model: str | None,
) -> int:
    first_harvest_day = growth_days + 1
    if first_harvest_day > available_days:
        return 0

    if special_harvest_model == "last_week_daily":
        return _max_harvests_last_week_daily(first_harvest_day=first_harvest_day, seasons_count=seasons_count)

    if regrowth_days <= 0:
        return 1

    return 1 + max(0, (available_days - first_harvest_day) // regrowth_days)


def _max_harvests_last_week_daily(first_harvest_day: int, seasons_count: int) -> int:
    harvests = 0
    for season_index in range(seasons_count):
        season_start = (season_index * SEASON_LENGTH_DAYS) + 1
        last_week_start = season_start + 21
        season_end = season_start + (SEASON_LENGTH_DAYS - 1)
        first_possible_harvest = max(first_harvest_day, last_week_start)
        if first_possible_harvest <= season_end:
            harvests += season_end - first_possible_harvest + 1
    return harvests


def _max_contiguous_window_days(seasons: list[str]) -> int:
    if not seasons:
        return SEASON_LENGTH_DAYS

    season_set = set(seasons)
    if all(season in season_set for season in SEASON_ORDER):
        return len(SEASON_ORDER) * SEASON_LENGTH_DAYS

    markers = [season in season_set for season in SEASON_ORDER]
    doubled = markers + markers
    best = 0
    current = 0

    for is_supported in doubled:
        if is_supported:
            current += 1
            if current > len(SEASON_ORDER):
                current = len(SEASON_ORDER)
            best = max(best, current)
        else:
            current = 0

    return max(1, best) * SEASON_LENGTH_DAYS


def _apply_season_override(crop_name: str, seasons: list[str]) -> list[str]:
    override = CROP_RULE_OVERRIDES.get(crop_name)
    if override and "valley_seasons" in override:
        return list(override["valley_seasons"])
    return seasons


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-")


def _serialise_seasons_list(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return "|".join(str(item) for item in value)
    return str(value)


def _parse_seasons_list(value: object) -> list[str]:
    if pd.isna(value):
        return []
    if isinstance(value, list):
        return value
    text = str(value).strip()
    if not text:
        return []
    return [item for item in text.split("|") if item]
