from __future__ import annotations

import math
from typing import Any

STRATEGIES = ("max_profit", "quick_cash", "low_effort", "balanced")


def rank_mix_candidates(rows: list[dict[str, Any]], strategy: str) -> list[dict[str, Any]]:
    eligible = [row for row in rows if _is_eligible(row)]
    if not eligible:
        return []

    strategy = strategy if strategy in STRATEGIES else "balanced"

    profit_total = [float(row["profit_total"]) for row in eligible]
    profit_day = [float(row["profit_per_day"]) for row in eligible]
    roi_values = [float(row["roi"]) for row in eligible]
    first_harvest = [float(row["first_harvest_day"]) for row in eligible]
    seed_cycles = [float(row.get("seed_cycles", 1)) for row in eligible]
    is_regrowable = [1.0 if bool(row.get("is_regrowable", False)) else 0.0 for row in eligible]

    p_norm = _norm(profit_total)
    d_norm = _norm(profit_day)
    r_norm = _norm(roi_values)
    f_norm = _norm_inverse(first_harvest)
    e_norm = _norm_inverse(seed_cycles)
    g_norm = _norm(is_regrowable)

    ranked: list[dict[str, Any]] = []
    for index, row in enumerate(eligible):
        harvest_count = int(row.get("harvest_count", 0))
        yield_per_harvest = float(row.get("yield_per_harvest", 1.0))
        sell_price = float(row.get("sell_price_effective", row.get("sell_price_raw", 0.0)))
        seed_price = float(row.get("seed_price", 0.0))
        seed_cycles = max(1, int(row.get("seed_cycles", 1)))
        window_days = max(1, int(row.get("window_days", 28)))

        per_tile_seed_cost = seed_price * seed_cycles
        per_tile_revenue = harvest_count * sell_price * yield_per_harvest
        per_tile_profit = per_tile_revenue - per_tile_seed_cost
        per_tile_profit_day = per_tile_profit / window_days

        score = _strategy_score(
            strategy=strategy,
            p=p_norm[index],
            d=d_norm[index],
            r=r_norm[index],
            f=f_norm[index],
            e=e_norm[index],
            g=g_norm[index],
        )

        ranked.append(
            {
                **row,
                "mix_score": score,
                "per_tile_seed_cost": per_tile_seed_cost,
                "per_tile_revenue": per_tile_revenue,
                "per_tile_profit": per_tile_profit,
                "per_tile_profit_day": per_tile_profit_day,
            }
        )

    return sorted(
        ranked,
        key=lambda item: (
            item["mix_score"],
            float(item["profit_total"]),
            float(item["profit_per_day"]),
            -float(item["first_harvest_day"]),
            item["crop_name"],
        ),
        reverse=True,
    )


def allocate_mix(
    candidates: list[dict[str, Any]],
    tiles: int,
    budget: float | None,
    cap_percent: int,
    top_n: int,
) -> dict[str, Any]:
    total_tiles = max(0, int(tiles))
    if total_tiles < 1 or not candidates:
        return _empty_mix_result(total_tiles=total_tiles, budget=budget)

    top_n = max(1, int(top_n))
    cap_percent = max(20, min(100, int(cap_percent)))
    cap_tiles = max(1, math.floor(total_tiles * (cap_percent / 100.0)))
    scoped = candidates[:top_n]

    allocation_map: dict[str, dict[str, Any]] = {}
    allocated_tiles = 0
    has_budget_limit = budget is not None
    budget_remaining = float("inf") if budget is None else max(0.0, float(budget))

    while allocated_tiles < total_tiles:
        progressed = False
        for candidate in scoped:
            if allocated_tiles >= total_tiles:
                break

            crop_id = str(candidate["crop_id"])
            current = allocation_map.get(crop_id)
            current_tiles = int(current["tiles"]) if current else 0
            if current_tiles >= cap_tiles:
                continue

            unit_cost = float(candidate["per_tile_seed_cost"])
            if unit_cost > budget_remaining:
                continue

            if current is None:
                current = _new_allocation_entry(candidate)
                allocation_map[crop_id] = current

            current["tiles"] += 1
            current["seed_cost"] += unit_cost
            current["revenue"] += float(candidate["per_tile_revenue"])
            current["profit"] += float(candidate["per_tile_profit"])
            current["profit_per_day"] += float(candidate["per_tile_profit_day"])
            budget_remaining -= unit_cost
            allocated_tiles += 1
            progressed = True

        if not progressed:
            break

    allocations = [allocation_map[cand["crop_id"]] for cand in scoped if cand["crop_id"] in allocation_map]
    total_seed_cost = sum(float(item["seed_cost"]) for item in allocations)
    total_revenue = sum(float(item["revenue"]) for item in allocations)
    total_profit = sum(float(item["profit"]) for item in allocations)
    total_profit_day = sum(float(item["profit_per_day"]) for item in allocations)
    unused_tiles = max(0, total_tiles - allocated_tiles)

    return {
        "allocations": allocations,
        "totals": {
            "total_tiles": total_tiles,
            "used_tiles": allocated_tiles,
            "unused_tiles": unused_tiles,
            "total_seed_cost": total_seed_cost,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "total_profit_per_day": total_profit_day,
            "budget_remaining": None if not has_budget_limit else max(0.0, budget_remaining),
            "cap_percent": cap_percent,
            "cap_tiles": cap_tiles,
            "budget_limited": has_budget_limit,
        },
    }


def summarize_mix(allocation_result: dict[str, Any]) -> dict[str, Any]:
    allocations = allocation_result.get("allocations", [])
    totals = allocation_result.get("totals", {})

    table_rows = []
    for item in allocations:
        table_rows.append(
            {
                "crop_id": item["crop_id"],
                "crop_name": item["crop_name"],
                "tiles": int(item["tiles"]),
                "seed_cost": round(float(item["seed_cost"]), 2),
                "harvest_count": int(item["harvest_count"]),
                "revenue": round(float(item["revenue"]), 2),
                "profit": round(float(item["profit"]), 2),
                "profit_per_day": round(float(item["profit_per_day"]), 2),
                "roi": round(float(item["roi"]), 3),
                "mix_score": round(float(item["mix_score"]), 4),
            }
        )

    return {
        "allocations": allocations,
        "table_rows": table_rows,
        "totals": totals,
    }


def _is_eligible(row: dict[str, Any]) -> bool:
    if not bool(row.get("profit_supported", True)):
        return False
    if not bool(row.get("can_mature", False)):
        return False
    return float(row.get("profit_total", 0.0)) > 0


def _strategy_score(strategy: str, p: float, d: float, r: float, f: float, e: float, g: float) -> float:
    if strategy == "max_profit":
        return (0.65 * p) + (0.20 * d) + (0.15 * r)
    if strategy == "quick_cash":
        return (0.50 * d) + (0.30 * f) + (0.20 * r)
    if strategy == "low_effort":
        return (0.45 * e) + (0.35 * g) + (0.20 * p)
    return (0.35 * p) + (0.25 * d) + (0.20 * r) + (0.20 * f)


def _norm(values: list[float]) -> list[float]:
    minimum = min(values)
    maximum = max(values)
    if math.isclose(minimum, maximum):
        return [1.0 for _ in values]
    return [(value - minimum) / (maximum - minimum) for value in values]


def _norm_inverse(values: list[float]) -> list[float]:
    minimum = min(values)
    maximum = max(values)
    if math.isclose(minimum, maximum):
        return [1.0 for _ in values]
    return [(maximum - value) / (maximum - minimum) for value in values]


def _new_allocation_entry(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "crop_id": candidate["crop_id"],
        "crop_name": candidate["crop_name"],
        "tiles": 0,
        "seed_cost": 0.0,
        "revenue": 0.0,
        "profit": 0.0,
        "profit_per_day": 0.0,
        "harvest_count": int(candidate["harvest_count"]),
        "roi": float(candidate["roi"]),
        "mix_score": float(candidate["mix_score"]),
    }


def _empty_mix_result(total_tiles: int, budget: float | None) -> dict[str, Any]:
    has_budget_limit = budget is not None
    return {
        "allocations": [],
        "totals": {
            "total_tiles": total_tiles,
            "used_tiles": 0,
            "unused_tiles": total_tiles,
            "total_seed_cost": 0.0,
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "total_profit_per_day": 0.0,
            "budget_remaining": None if not has_budget_limit else max(0.0, float(budget or 0.0)),
            "cap_percent": 60,
            "cap_tiles": max(1, math.floor(total_tiles * 0.6)) if total_tiles > 0 else 0,
            "budget_limited": has_budget_limit,
        },
    }
