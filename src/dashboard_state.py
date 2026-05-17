from __future__ import annotations

import math
from typing import Any

from .constants import SEASON_LENGTH_DAYS, SEASON_ORDER
from .data_loader import load_clean_crops
from .farm_math import compute_crop_profit

SEASON_OPTIONS = [{"label": season, "value": season} for season in SEASON_ORDER]

GOAL_OPTIONS = [
    {"label": "Max total profit", "value": "profit_total"},
    {"label": "Max profit per day", "value": "profit_per_day"},
    {"label": "Max ROI", "value": "roi"},
    {"label": "Fastest first harvest", "value": "time_to_first_harvest"},
]

FERTILIZER_OPTIONS = [
    {"label": "None", "value": "none"},
    {"label": "Speed-Gro (approx)", "value": "speed_gro"},
    {"label": "Deluxe Speed-Gro (approx)", "value": "deluxe_speed_gro"},
]

DEFAULT_FILTERS = {
    "season": "Spring",
    "current_day": 1,
    "tiles": 80,
    "budget": 5000.0,
    "fertilizer": "none",
}

_GOAL_VALUES = {option["value"] for option in GOAL_OPTIONS}
_FERTILIZER_GROWTH_FACTOR = {"none": 1.0, "speed_gro": 0.9, "deluxe_speed_gro": 0.75}
_CROPS_DF = load_clean_crops()


def build_filtered_snapshot(
    season: str | None,
    current_day: int | None,
    tiles: int | None,
    budget: float | int | str | None,
    goal: str | None,
    fertilizer: str | None,
) -> dict[str, Any]:
    normalized = _normalize_filters(
        season=season,
        current_day=current_day,
        tiles=tiles,
        budget=budget,
        goal=goal,
        fertilizer=fertilizer,
    )

    rows: list[dict[str, Any]] = []
    budget_value = normalized["budget"]
    season_name = normalized["season"]

    for _, crop in _CROPS_DF.iterrows():
        seasons_list = crop["seasons_list"] if isinstance(crop["seasons_list"], list) else []
        if season_name not in seasons_list:
            continue
        if not bool(crop.get("profit_supported", True)):
            continue

        window_days = _remaining_window_days(
            season=season_name,
            current_day=normalized["current_day"],
            seasons_list=seasons_list,
        )
        if window_days <= 0:
            continue

        growth_days = int(crop["growth_days"])
        adjusted_growth_days = max(
            1,
            math.ceil(growth_days * _FERTILIZER_GROWTH_FACTOR[normalized["fertilizer"]]),
        )
        adjusted_sell_price = float(crop["sell_price_raw"])
        regrowth_days = int(crop["regrowth_days"])

        metrics = compute_crop_profit(
            seed_price=float(crop["seed_price"]),
            sell_price=adjusted_sell_price,
            growth_days=adjusted_growth_days,
            regrowth_days=regrowth_days if regrowth_days > 0 else None,
            current_day=1,
            tiles=normalized["tiles"],
            yield_per_harvest=float(crop["yield_per_harvest"]),
            budget=budget_value,
            season_length=window_days,
            special_harvest_model=(str(crop.get("special_harvest_model") or "") or None),
        )

        warning_flags = _build_warning_flags(
            can_mature=bool(metrics["can_mature"]),
            affordable=metrics["affordable"],
            is_trellis=bool(crop["is_trellis"]),
            is_quest_only=bool(crop["is_quest_only"]),
        )

        row = {
            "crop_id": str(crop["crop_id"]),
            "crop_name": str(crop["crop_name"]),
            "season": str(crop["season"]),
            "window_days": window_days,
            "growth_days": adjusted_growth_days,
            "base_growth_days": growth_days,
            "regrowth_days": int(crop["regrowth_days"]),
            "seed_price": float(crop["seed_price"]),
            "sell_price_raw": float(crop["sell_price_raw"]),
            "sell_price_effective": adjusted_sell_price,
            "base_yield": float(crop["base_yield"]),
            "expected_extra_yield": float(crop.get("expected_extra_yield", 0.0)),
            "yield_per_harvest": float(crop["yield_per_harvest"]),
            "seed_cycles": int(metrics.get("seed_cycles", 0)),
            "harvest_count": int(metrics["harvest_count"]),
            "revenue": float(metrics["revenue"]),
            "seed_cost": float(metrics["seed_cost"]),
            "profit_total": float(metrics["profit"]),
            "profit_per_day": float(metrics["profit_per_day"]),
            "roi": float(metrics["roi"]),
            "affordable": metrics["affordable"],
            "can_mature": bool(metrics["can_mature"]),
            "first_harvest_day": adjusted_growth_days + 1,
            "is_regrowable": bool(crop["is_regrowable"]),
            "is_trellis": bool(crop["is_trellis"]),
            "is_quest_only": bool(crop["is_quest_only"]),
            "profit_supported": bool(crop.get("profit_supported", True)),
            "special_harvest_model": str(crop.get("special_harvest_model", "")),
            "farm_context": str(crop.get("farm_context", "")),
            "seed_price_model": str(crop.get("seed_price_model", "")),
            "yield_note": str(crop.get("yield_note", "")),
            "rule_note": str(crop["rule_note"]),
            "warning_flags": warning_flags,
        }
        row["goal_score"] = _goal_score(normalized["goal"], row)
        rows.append(row)

    rows = _sort_rows(rows, normalized["goal"])
    selected = rows[0] if rows else None

    summary = _build_summary(normalized, len(rows), selected)
    return {
        "filters": normalized,
        "rows": rows,
        "selected_crop": selected,
        "summary": summary,
    }


def _normalize_filters(
    season: str | None,
    current_day: int | None,
    tiles: int | None,
    budget: float | int | str | None,
    goal: str | None,
    fertilizer: str | None,
) -> dict[str, Any]:
    normalized = dict(DEFAULT_FILTERS)
    normalized["goal"] = "profit_per_day"

    if season in SEASON_ORDER:
        normalized["season"] = season

    normalized["current_day"] = _clamp_int(current_day, DEFAULT_FILTERS["current_day"], 1, SEASON_LENGTH_DAYS)
    normalized["tiles"] = _clamp_int(tiles, DEFAULT_FILTERS["tiles"], 0, 5000)

    parsed_budget = _parse_budget(budget)
    if parsed_budget is not None:
        normalized["budget"] = parsed_budget
    else:
        normalized["budget"] = None

    if goal in _GOAL_VALUES:
        normalized["goal"] = goal

    if fertilizer in _FERTILIZER_GROWTH_FACTOR:
        normalized["fertilizer"] = fertilizer

    return normalized


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _parse_budget(value: float | int | str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, parsed)


def _remaining_window_days(season: str, current_day: int, seasons_list: list[str]) -> int:
    season_set = set(seasons_list)
    if season not in season_set:
        return 0

    start_index = SEASON_ORDER.index(season)
    contiguous_supported_seasons = 0

    for offset in range(len(SEASON_ORDER)):
        checked_season = SEASON_ORDER[(start_index + offset) % len(SEASON_ORDER)]
        if checked_season in season_set:
            contiguous_supported_seasons += 1
        else:
            break

    current_season_days = SEASON_LENGTH_DAYS - current_day + 1
    future_days = max(0, contiguous_supported_seasons - 1) * SEASON_LENGTH_DAYS
    return current_season_days + future_days


def _goal_score(goal: str, row: dict[str, Any]) -> float:
    if goal == "time_to_first_harvest":
        return -float(row["first_harvest_day"])
    return float(row[goal])


def _sort_rows(rows: list[dict[str, Any]], goal: str) -> list[dict[str, Any]]:
    if goal == "time_to_first_harvest":
        return sorted(
            rows,
            key=lambda item: (item["first_harvest_day"], -item["profit_total"], -item["roi"], item["crop_name"]),
        )

    return sorted(
        rows,
        key=lambda item: (item[goal], item["profit_total"], -item["first_harvest_day"]),
        reverse=True,
    )


def _build_warning_flags(
    can_mature: bool,
    affordable: bool | None,
    is_trellis: bool,
    is_quest_only: bool,
) -> list[str]:
    flags: list[str] = []
    if not can_mature:
        flags.append("Too Late")
    if affordable is False:
        flags.append("Over Budget")
    if is_trellis:
        flags.append("Trellis")
    if is_quest_only:
        flags.append("Quest-only")
    return flags


def _build_summary(
    filters: dict[str, Any],
    row_count: int,
    selected: dict[str, Any] | None,
) -> str:
    base = (
        f"{filters['season']} day {filters['current_day']}, {filters['tiles']} tiles, "
        f"goal: {filters['goal'].replace('_', ' ')}."
    )
    if row_count == 0 or selected is None:
        return f"{base} No crops match the current filters."
    return (
        f"{base} {row_count} matching crops. Top pick: {selected['crop_name']} "
        f"({selected['profit_total']:.0f}g total, {selected['profit_per_day']:.1f}g/day)."
    )
