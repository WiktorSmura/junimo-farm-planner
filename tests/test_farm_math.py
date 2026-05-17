import pytest

from src.farm_math import can_mature, compute_crop_profit, compute_harvest_count, compute_harvest_schedule, days_left_in_season


def test_days_left_in_season_handles_edges():
    assert days_left_in_season(1) == 28
    assert days_left_in_season(28) == 1
    assert days_left_in_season(29) == 0


def test_days_left_invalid_season_length_raises():
    with pytest.raises(ValueError):
        days_left_in_season(1, season_length=0)


def test_can_mature():
    assert can_mature(current_day=10, growth_days=5) is True
    assert can_mature(current_day=28, growth_days=2) is False
    assert can_mature(current_day=5, growth_days=0) is False


def test_compute_harvest_count_non_regrowing_replant_model():
    assert compute_harvest_count(current_day=1, growth_days=7, regrowth_days=None) == 3
    assert compute_harvest_count(current_day=28, growth_days=2, regrowth_days=None) == 0


def test_compute_harvest_count_regrowing():
    assert compute_harvest_count(current_day=1, growth_days=10, regrowth_days=3) == 6
    assert compute_harvest_count(current_day=20, growth_days=12, regrowth_days=4) == 0


def test_compute_crop_profit_non_regrowing():
    result = compute_crop_profit(
        seed_price=20,
        sell_price=35,
        growth_days=4,
        regrowth_days=None,
        current_day=1,
        tiles=10,
    )

    assert result["can_mature"] is True
    assert result["days_left"] == 28
    assert result["harvest_count"] == 6
    assert result["seed_cost"] == 1200.0
    assert result["revenue"] == 2100.0
    assert result["profit"] == 900.0
    assert result["profit_per_day"] == 900.0 / 28.0


def test_compute_crop_profit_regrowing():
    result = compute_crop_profit(
        seed_price=60,
        sell_price=40,
        growth_days=10,
        regrowth_days=3,
        current_day=1,
        tiles=10,
    )

    assert result["harvest_count"] == 6
    assert result["seed_cost"] == 600.0
    assert result["revenue"] == 2400.0
    assert result["profit"] == 1800.0
    assert result["roi"] == pytest.approx(1800.0 / 600.0)


def test_compute_crop_profit_handles_zero_tiles_and_unmatured_crop():
    zero_tiles = compute_crop_profit(
        seed_price=50,
        sell_price=100,
        growth_days=5,
        regrowth_days=None,
        current_day=1,
        tiles=0,
    )
    assert zero_tiles["harvest_count"] == 0
    assert zero_tiles["profit"] == 0.0

    too_late = compute_crop_profit(
        seed_price=50,
        sell_price=100,
        growth_days=4,
        regrowth_days=None,
        current_day=28,
        tiles=10,
    )
    assert too_late["can_mature"] is False
    assert too_late["harvest_count"] == 0
    assert too_late["profit"] == 0.0


def test_compute_crop_profit_budget_flag():
    unaffordable = compute_crop_profit(
        seed_price=80,
        sell_price=120,
        growth_days=8,
        regrowth_days=None,
        current_day=1,
        tiles=10,
        budget=0,
    )
    assert unaffordable["affordable"] is False

    affordable = compute_crop_profit(
        seed_price=20,
        sell_price=50,
        growth_days=10,
        regrowth_days=5,
        current_day=1,
        tiles=5,
        budget=200,
    )
    assert affordable["affordable"] is True


def test_compute_harvest_schedule_matches_count():
    schedule = compute_harvest_schedule(
        seed_price=20,
        sell_price=50,
        growth_days=4,
        regrowth_days=None,
        current_day=1,
        tiles=10,
    )
    harvests = [e for e in schedule if e["event"] == "Harvest"]
    assert len(harvests) == 6

    schedule_regrow = compute_harvest_schedule(
        seed_price=60,
        sell_price=40,
        growth_days=10,
        regrowth_days=3,
        current_day=1,
        tiles=10,
    )
    harvests_regrow = [e for e in schedule_regrow if e["event"] == "Harvest"]
    assert len(harvests_regrow) == 6
