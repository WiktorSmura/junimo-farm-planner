from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .constants import (
    BASE_YIELD_OVERRIDES,
    CLEAN_CROPS_FILE,
    CROP_NUMERIC_OVERRIDES,
    CROP_RULE_OVERRIDES,
    EXPECTED_EXTRA_YIELD_OVERRIDES,
    MANUAL_RAW_CROP_ROWS,
    RANDOM_EXTRA_YIELD_NOTES,
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
    "seed_price_model",
    "sell_price_raw",
    "growth_days",
    "regrowth_days",
    "is_regrowable",
    "is_trellis",
    "is_multi_season",
    "is_quest_only",
    "profit_supported",
    "farm_context",
    "rule_note",
    "special_harvest_model",
    "available_days",
    "base_yield",
    "expected_extra_yield",
    "yield_per_harvest",
    "yield_note",
    "max_harvests",
    "seed_cycles",
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
    df = _append_manual_rows(df)
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
    cleaned = _apply_numeric_overrides(cleaned)

    grouped_rows = []
    for crop_name, group in cleaned.groupby("crop_name", sort=True):
        rule_override = CROP_RULE_OVERRIDES.get(crop_name, {})
        seasons = _merge_seasons(group["season"].tolist())
        seasons = _apply_season_override(crop_name, seasons)
        season_label = _season_label(seasons)

        growth_days = int(group["days_to_grow"].iloc[0]) if pd.notna(group["days_to_grow"].iloc[0]) else 0
        regrowth_days = int(group["regrowth"].iloc[0]) if pd.notna(group["regrowth"].iloc[0]) else 0
        seed_price = int(group["seed_price"].iloc[0]) if pd.notna(group["seed_price"].iloc[0]) else 0
        sell_price_raw = int(group["sell_price"].iloc[0]) if pd.notna(group["sell_price"].iloc[0]) else 0

        is_regrowable = bool(regrowth_days > 0 or group["multiple_harvests"].fillna(False).any())
        is_trellis = crop_name in TRELLIS_CROPS
        available_days = _max_contiguous_window_days(seasons)
        base_yield = float(BASE_YIELD_OVERRIDES.get(crop_name, 1.0))
        expected_extra_yield = float(EXPECTED_EXTRA_YIELD_OVERRIDES.get(crop_name, 0.0))
        yield_per_harvest = base_yield + expected_extra_yield
        first_harvest_day = growth_days + 1 if growth_days > 0 else pd.NA
        will_mature = bool(growth_days > 0 and first_harvest_day <= available_days)

        max_harvests = _max_harvests(
            crop_name=crop_name,
            growth_days=growth_days,
            regrowth_days=regrowth_days,
            available_days=available_days,
            seasons_count=len(seasons),
            special_harvest_model=rule_override.get("special_harvest_model"),
        )
        seed_cycles = _seed_cycles(
            max_harvests=max_harvests,
            regrowth_days=regrowth_days,
            special_harvest_model=rule_override.get("special_harvest_model"),
        )

        profit_supported = bool(rule_override.get("profit_supported", True))
        revenue = max_harvests * sell_price_raw * yield_per_harvest
        seed_cost = seed_cycles * seed_price
        profit_total = revenue - seed_cost if profit_supported else pd.NA
        profit_per_day = (profit_total / available_days) if profit_supported and available_days > 0 else pd.NA
        roi = (profit_total / seed_cost) if profit_supported and seed_cost > 0 else (pd.NA if not profit_supported else 0.0)
        affordable = pd.NA

        grouped_rows.append(
            {
                "crop_id": _slugify(crop_name),
                "crop_name": crop_name,
                "season": season_label,
                "seasons_list": seasons,
                "description": group["description"].iloc[0],
                "seed_price": seed_price,
                "seed_price_model": rule_override.get("seed_price_model", "shop_gold"),
                "sell_price_raw": sell_price_raw,
                "growth_days": growth_days,
                "regrowth_days": regrowth_days,
                "is_regrowable": is_regrowable,
                "is_trellis": is_trellis,
                "is_multi_season": len(seasons) > 1,
                "is_quest_only": bool(rule_override.get("quest_only", False)),
                "profit_supported": profit_supported,
                "farm_context": rule_override.get("farm_context", "standard_outdoor"),
                "rule_note": rule_override.get("rule_note", ""),
                "special_harvest_model": rule_override.get("special_harvest_model", ""),
                "available_days": available_days,
                "base_yield": base_yield,
                "expected_extra_yield": expected_extra_yield,
                "yield_per_harvest": yield_per_harvest,
                "yield_note": RANDOM_EXTRA_YIELD_NOTES.get(crop_name, ""),
                "max_harvests": max_harvests,
                "seed_cycles": seed_cycles,
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


def _append_manual_rows(df: pd.DataFrame) -> pd.DataFrame:
    if not MANUAL_RAW_CROP_ROWS:
        return df
    existing_names = set(df.get("crop_name", pd.Series(dtype=str)).astype(str).str.strip())
    rows = [row for row in MANUAL_RAW_CROP_ROWS if row["crop_name"] not in existing_names]
    if not rows:
        return df
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)


def _apply_numeric_overrides(df: pd.DataFrame) -> pd.DataFrame:
    updated = df.copy()
    for crop_name, overrides in CROP_NUMERIC_OVERRIDES.items():
        mask = updated["crop_name"] == crop_name
        if not mask.any():
            continue
        for raw_column, value in overrides.items():
            if raw_column == "growth_days":
                column = "days_to_grow"
            elif raw_column == "regrowth_days":
                column = "regrowth"
            elif raw_column == "sell_price_raw":
                column = "sell_price"
            else:
                column = raw_column
            if column in updated.columns:
                updated.loc[mask, column] = value
    return updated


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
    if growth_days < 1 or available_days < 1:
        return 0

    first_harvest_day = growth_days + 1
    if first_harvest_day > available_days:
        return 0

    if special_harvest_model == "last_week_daily":
        return _max_harvests_last_week_daily(first_harvest_day=first_harvest_day, seasons_count=seasons_count)

    if regrowth_days <= 0:
        # Planting on day 1 with N growth days harvests on day 1+N.
        # Therefore only available_days - 1 nights can be used for harvest cycles.
        return (available_days - 1) // growth_days

    return 1 + max(0, (available_days - first_harvest_day) // regrowth_days)


def _seed_cycles(max_harvests: int, regrowth_days: int, special_harvest_model: str | None) -> int:
    if max_harvests < 1:
        return 0
    if special_harvest_model is not None:
        return 1
    return 1 if regrowth_days > 0 else max_harvests


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
