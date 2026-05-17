from src.dashboard_state import build_filtered_snapshot


def test_snapshot_filters_by_season_and_search():
    snapshot = build_filtered_snapshot(
        season="Summer",
        current_day=1,
        tiles=40,
        budget=5000,
        goal="profit_per_day",
        processing_mode="raw",
        fertilizer="none",
        search_term="corn",
    )

    assert snapshot["rows"]
    assert all(row["crop_name"] == "Corn" for row in snapshot["rows"])


def test_snapshot_day_changes_feasibility():
    early = build_filtered_snapshot(
        season="Spring",
        current_day=1,
        tiles=80,
        budget=5000,
        goal="profit_total",
        processing_mode="raw",
        fertilizer="none",
        search_term="cauliflower",
    )
    late = build_filtered_snapshot(
        season="Spring",
        current_day=25,
        tiles=80,
        budget=5000,
        goal="profit_total",
        processing_mode="raw",
        fertilizer="none",
        search_term="cauliflower",
    )

    assert early["rows"][0]["can_mature"] is True
    assert late["rows"][0]["can_mature"] is False


def test_snapshot_budget_changes_affordability():
    affordable = build_filtered_snapshot(
        season="Summer",
        current_day=1,
        tiles=20,
        budget=5000,
        goal="profit_per_day",
        processing_mode="raw",
        fertilizer="none",
        search_term="melon",
    )
    over_budget = build_filtered_snapshot(
        season="Summer",
        current_day=1,
        tiles=20,
        budget=100,
        goal="profit_per_day",
        processing_mode="raw",
        fertilizer="none",
        search_term="melon",
    )

    assert affordable["rows"][0]["affordable"] is True
    assert over_budget["rows"][0]["affordable"] is False


def test_snapshot_invalid_inputs_are_handled():
    snapshot = build_filtered_snapshot(
        season="NotASeason",
        current_day="x",
        tiles="y",
        budget="oops",
        goal="unknown-goal",
        processing_mode="unknown-processing",
        fertilizer="unknown-fertilizer",
        search_term=None,
    )

    assert snapshot["rows"]
    assert snapshot["filters"]["season"] == "Spring"
    assert snapshot["filters"]["current_day"] == 1
    assert snapshot["filters"]["tiles"] == 80
    assert snapshot["filters"]["goal"] == "profit_per_day"
