from src.farm_mix import allocate_mix, rank_mix_candidates, summarize_mix


def _rows():
    return [
        {
            "crop_id": "a",
            "crop_name": "A",
            "profit_supported": True,
            "can_mature": True,
            "profit_total": 1000.0,
            "profit_per_day": 50.0,
            "roi": 2.0,
            "first_harvest_day": 8,
            "seed_cycles": 4,
            "is_regrowable": False,
            "harvest_count": 4,
            "seed_price": 25.0,
            "sell_price_effective": 70.0,
            "yield_per_harvest": 1.0,
            "window_days": 28,
        },
        {
            "crop_id": "b",
            "crop_name": "B",
            "profit_supported": True,
            "can_mature": True,
            "profit_total": 800.0,
            "profit_per_day": 28.0,
            "roi": 3.4,
            "first_harvest_day": 6,
            "seed_cycles": 1,
            "is_regrowable": True,
            "harvest_count": 8,
            "seed_price": 60.0,
            "sell_price_effective": 55.0,
            "yield_per_harvest": 1.0,
            "window_days": 28,
        },
        {
            "crop_id": "c",
            "crop_name": "C",
            "profit_supported": True,
            "can_mature": True,
            "profit_total": 500.0,
            "profit_per_day": 18.0,
            "roi": 1.4,
            "first_harvest_day": 5,
            "seed_cycles": 7,
            "is_regrowable": False,
            "harvest_count": 7,
            "seed_price": 10.0,
            "sell_price_effective": 28.0,
            "yield_per_harvest": 1.0,
            "window_days": 28,
        },
        {
            "crop_id": "x",
            "crop_name": "Unsupported",
            "profit_supported": False,
            "can_mature": True,
            "profit_total": 9999.0,
            "profit_per_day": 999.0,
            "roi": 99.0,
            "first_harvest_day": 2,
            "seed_cycles": 1,
            "is_regrowable": True,
            "harvest_count": 10,
            "seed_price": 1.0,
            "sell_price_effective": 100.0,
            "yield_per_harvest": 1.0,
            "window_days": 28,
        },
    ]


def test_allocate_mix_respects_tile_constraint():
    ranked = rank_mix_candidates(_rows(), strategy="balanced")
    result = allocate_mix(ranked, tiles=30, budget=10_000, cap_percent=60, top_n=8)

    totals = result["totals"]
    assert totals["used_tiles"] <= 30
    assert totals["unused_tiles"] == 30 - totals["used_tiles"]


def test_allocate_mix_respects_budget_constraint():
    ranked = rank_mix_candidates(_rows(), strategy="balanced")
    result = allocate_mix(ranked, tiles=80, budget=500, cap_percent=60, top_n=8)

    totals = result["totals"]
    assert totals["total_seed_cost"] <= 500
    assert totals["budget_remaining"] >= 0


def test_allocate_mix_respects_concentration_cap():
    ranked = rank_mix_candidates(_rows(), strategy="max_profit")
    result = allocate_mix(ranked, tiles=20, budget=10_000, cap_percent=40, top_n=8)

    max_tiles = max((item["tiles"] for item in result["allocations"]), default=0)
    assert max_tiles <= 8


def test_strategy_switch_changes_ranking_order():
    ranked_profit = rank_mix_candidates(_rows(), strategy="max_profit")
    ranked_effort = rank_mix_candidates(_rows(), strategy="low_effort")

    assert ranked_profit
    assert ranked_effort
    assert ranked_profit[0]["crop_id"] != ranked_effort[0]["crop_id"]


def test_no_eligible_rows_returns_empty_safe_payload():
    rows = [{**row, "profit_supported": False} for row in _rows()]
    ranked = rank_mix_candidates(rows, strategy="balanced")
    result = allocate_mix(ranked, tiles=20, budget=1000, cap_percent=60, top_n=8)
    summary = summarize_mix(result)

    assert ranked == []
    assert summary["allocations"] == []
    assert summary["table_rows"] == []
    assert summary["totals"]["used_tiles"] == 0


def test_summarize_mix_table_matches_totals():
    ranked = rank_mix_candidates(_rows(), strategy="balanced")
    result = allocate_mix(ranked, tiles=24, budget=5000, cap_percent=60, top_n=8)
    summary = summarize_mix(result)

    table_seed_cost = sum(row["seed_cost"] for row in summary["table_rows"])
    table_profit = sum(row["profit"] for row in summary["table_rows"])
    assert round(table_seed_cost, 2) == round(summary["totals"]["total_seed_cost"], 2)
    assert round(table_profit, 2) == round(summary["totals"]["total_profit"], 2)
