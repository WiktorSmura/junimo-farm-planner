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
    if current_day < 1:
        current_day = 1
    if current_day > season_length:
        return False
    # A crop planted on day D with N growth days is harvested on day D + N.
    # Example: Parsnip planted Spring 1 with 4 growth days is harvested Spring 5.
    return current_day + growth_days <= season_length


def compute_harvest_count(
    current_day: int,
    growth_days: int,
    regrowth_days: int | None,
    season_length: int = 28,
    special_harvest_model: str | None = None,
) -> int:
    if season_length < 1:
        raise ValueError("season_length must be at least 1")

    if current_day < 1:
        current_day = 1
    if current_day > season_length or growth_days < 1:
        return 0

    if special_harvest_model == "last_week_daily":
        return _compute_last_week_daily_harvest_count(
            current_day=current_day,
            growth_days=growth_days,
            season_length=season_length,
        )

    first_harvest_day = current_day + growth_days
    if first_harvest_day > season_length:
        return 0

    # Non-regrowing crops are replanted immediately after each harvest.
    if regrowth_days is None or regrowth_days < 1:
        return (season_length - current_day) // growth_days

    return 1 + ((season_length - first_harvest_day) // regrowth_days)


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
    special_harvest_model: str | None = None,
) -> dict[str, Any]:
    days_left = days_left_in_season(current_day=current_day, season_length=season_length)
    if days_left < 1 or tiles < 1 or yield_per_harvest <= 0:
        return _empty_profit_result(days_left=days_left, budget=budget)

    harvest_count = compute_harvest_count(
        current_day=current_day,
        growth_days=growth_days,
        regrowth_days=regrowth_days,
        season_length=season_length,
        special_harvest_model=special_harvest_model,
    )
    if harvest_count < 1:
        return _empty_profit_result(days_left=days_left, budget=budget)

    is_regrowing = regrowth_days is not None and regrowth_days > 0
    seed_cycles = 1 if is_regrowing or special_harvest_model is not None else harvest_count
    seed_cost = float(seed_price) * float(tiles) * float(seed_cycles)
    revenue = float(harvest_count) * float(sell_price) * float(yield_per_harvest) * float(tiles)
    profit = revenue - seed_cost
    roi = 0.0 if seed_cost == 0 else profit / seed_cost
    profit_per_day = profit / max(1, days_left)

    return {
        "days_left": days_left,
        "can_mature": True,
        "harvest_count": harvest_count,
        "seed_cycles": seed_cycles,
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
        "seed_cycles": 0,
        "revenue": 0.0,
        "seed_cost": 0.0,
        "profit": 0.0,
        "roi": 0.0,
        "profit_per_day": 0.0,
        "seed_cost_model": "replant_non_regrow_once_for_regrow",
        "affordable": None if budget is None else True,
    }


def compute_harvest_schedule(
    seed_price: float,
    sell_price: float,
    growth_days: int,
    regrowth_days: int | None,
    current_day: int,
    tiles: int,
    yield_per_harvest: float = 1.0,
    season_length: int = 28,
    special_harvest_model: str | None = None,
) -> list[dict[str, Any]]:
    schedule = []
    if current_day < 1:
        current_day = 1

    days_left = days_left_in_season(current_day=current_day, season_length=season_length)
    if days_left < 1 or growth_days < 1 or tiles < 1:
        return schedule

    harvest_count = compute_harvest_count(
        current_day=current_day,
        growth_days=growth_days,
        regrowth_days=regrowth_days,
        season_length=season_length,
        special_harvest_model=special_harvest_model,
    )

    if harvest_count < 1:
        return schedule

    if special_harvest_model == "last_week_daily":
        return _compute_last_week_daily_schedule(
            seed_price=seed_price,
            sell_price=sell_price,
            growth_days=growth_days,
            current_day=current_day,
            tiles=tiles,
            yield_per_harvest=yield_per_harvest,
            season_length=season_length,
        )

    is_regrowing = regrowth_days is not None and regrowth_days > 0
    total_cost = 0.0
    total_revenue = 0.0
    cost_per_planting = seed_price * tiles
    rev_per_harvest = sell_price * tiles * yield_per_harvest

    day = current_day

    if is_regrowing:
        # One-time planting
        total_cost += cost_per_planting
        schedule.append(
            {
                "day": day,
                "event": "Plant",
                "revenue": 0.0,
                "cost": cost_per_planting,
                "profit": -cost_per_planting,
                "cumulative_profit": total_revenue - total_cost,
            }
        )
        harvest_day = day + growth_days
        for _ in range(harvest_count):
            total_revenue += rev_per_harvest
            schedule.append(
                {
                    "day": harvest_day,
                    "event": "Harvest",
                    "revenue": rev_per_harvest,
                    "cost": 0.0,
                    "profit": rev_per_harvest,
                    "cumulative_profit": total_revenue - total_cost,
                }
            )
            harvest_day += int(regrowth_days)
    else:
        # Replanting non-regrowing crops
        harvest_day = day + growth_days
        for _ in range(harvest_count):
            total_cost += cost_per_planting
            schedule.append(
                {
                    "day": day,
                    "event": "Plant",
                    "revenue": 0.0,
                    "cost": cost_per_planting,
                    "profit": -cost_per_planting,
                    "cumulative_profit": total_revenue - total_cost,
                }
            )
            total_revenue += rev_per_harvest
            schedule.append(
                {
                    "day": harvest_day,
                    "event": "Harvest",
                    "revenue": rev_per_harvest,
                    "cost": 0.0,
                    "profit": rev_per_harvest,
                    "cumulative_profit": total_revenue - total_cost,
                }
            )
            day = harvest_day
            harvest_day = day + growth_days

    return schedule


def _compute_last_week_daily_harvest_count(current_day: int, growth_days: int, season_length: int) -> int:
    # Tea Bush model: after maturity, it produces each day during days 22-28.
    maturity_day = current_day + growth_days
    first_harvest_day = max(maturity_day, 22)
    last_harvest_day = min(season_length, 28)
    if first_harvest_day > last_harvest_day:
        return 0
    return last_harvest_day - first_harvest_day + 1


def _compute_last_week_daily_schedule(
    seed_price: float,
    sell_price: float,
    growth_days: int,
    current_day: int,
    tiles: int,
    yield_per_harvest: float,
    season_length: int,
) -> list[dict[str, Any]]:
    schedule = []
    total_cost = seed_price * tiles
    total_revenue = 0.0
    rev_per_harvest = sell_price * tiles * yield_per_harvest

    schedule.append(
        {
            "day": current_day,
            "event": "Plant",
            "revenue": 0.0,
            "cost": total_cost,
            "profit": -total_cost,
            "cumulative_profit": -total_cost,
        }
    )

    maturity_day = current_day + growth_days
    first_harvest_day = max(maturity_day, 22)
    last_harvest_day = min(season_length, 28)

    for day in range(first_harvest_day, last_harvest_day + 1):
        total_revenue += rev_per_harvest
        schedule.append(
            {
                "day": day,
                "event": "Harvest",
                "revenue": rev_per_harvest,
                "cost": 0.0,
                "profit": rev_per_harvest,
                "cumulative_profit": total_revenue - total_cost,
            }
        )

    return schedule
