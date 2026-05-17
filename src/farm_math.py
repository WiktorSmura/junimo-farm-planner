from __future__ import annotations

from typing import Any


def days_left_in_season(current_day: int, season_length: int = 28) -> int:
    if season_length < 1:
        raise ValueError("season_length must be at least 1")

    if current_day < 1:
        return season_length
    if current_day > season_length:
        return 0
    return season_length - current_day + 1


def can_mature(current_day: int, growth_days: int, season_length: int = 28) -> bool:
    if growth_days < 1:
        return False
    return growth_days <= days_left_in_season(current_day=current_day, season_length=season_length)


def compute_harvest_count(
    current_day: int,
    growth_days: int,
    regrowth_days: int | None,
    season_length: int = 28,
) -> int:
    days_left = days_left_in_season(current_day=current_day, season_length=season_length)
    if days_left < 1 or growth_days < 1:
        return 0

    # Non-regrowing crops are replanted after each harvest.
    if regrowth_days is None or regrowth_days < 1:
        return days_left // growth_days

    if growth_days > days_left:
        return 0
    return 1 + ((days_left - growth_days) // regrowth_days)


def compute_crop_profit(
    seed_price: float,
    sell_price: float,
    growth_days: int,
    regrowth_days: int | None,
    current_day: int,
    tiles: int,
    yield_per_harvest: float = 1.0,
    budget: float | None = None,
    season_length: int = 28,
) -> dict[str, Any]:
    days_left = days_left_in_season(current_day=current_day, season_length=season_length)
    if days_left < 1 or tiles < 1 or yield_per_harvest <= 0:
        return _empty_profit_result(days_left=days_left, budget=budget)

    harvest_count = compute_harvest_count(
        current_day=current_day,
        growth_days=growth_days,
        regrowth_days=regrowth_days,
        season_length=season_length,
    )
    if harvest_count < 1:
        return _empty_profit_result(days_left=days_left, budget=budget)

    is_regrowing = regrowth_days is not None and regrowth_days > 0
    seed_cycles = 1 if is_regrowing else harvest_count
    seed_cost = float(seed_price) * float(tiles) * float(seed_cycles)
    revenue = float(harvest_count) * float(sell_price) * float(yield_per_harvest) * float(tiles)
    profit = revenue - seed_cost
    roi = 0.0 if seed_cost == 0 else profit / seed_cost
    profit_per_day = profit / days_left

    return {
        "days_left": days_left,
        "can_mature": True,
        "harvest_count": harvest_count,
        "revenue": revenue,
        "seed_cost": seed_cost,
        "profit": profit,
        "roi": roi,
        "profit_per_day": profit_per_day,
        "seed_cost_model": "replant_non_regrow_once_for_regrow",
        "affordable": None if budget is None else seed_cost <= budget,
    }


def _empty_profit_result(days_left: int, budget: float | None) -> dict[str, Any]:
    return {
        "days_left": max(0, days_left),
        "can_mature": False,
        "harvest_count": 0,
        "revenue": 0.0,
        "seed_cost": 0.0,
        "profit": 0.0,
        "roi": 0.0,
        "profit_per_day": 0.0,
        "seed_cost_model": "replant_non_regrow_once_for_regrow",
        "affordable": None if budget is None else True,
    }
