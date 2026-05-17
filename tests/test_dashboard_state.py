from src.dashboard_state import build_filtered_snapshot


def test_snapshot_filters_by_season():
    snapshot = build_filtered_snapshot(
        season="Summer",
        current_day=1,
        tiles=40,
        budget=5000,
        goal="profit_per_day",
        fertilizer="none",
    )

    assert snapshot["rows"]
    assert all("Summer" in row["season"] or row["season"] == "Any" for row in snapshot["rows"])


def test_snapshot_day_changes_feasibility():
    early = build_filtered_snapshot(
        season="Spring",
        current_day=1,
        tiles=80,
        budget=5000,
        goal="profit_total",
        fertilizer="none",
    )
    late = build_filtered_snapshot(
        season="Spring",
        current_day=25,
        tiles=80,
        budget=5000,
        goal="profit_total",
        fertilizer="none",
    )

    early_cauli = next(row for row in early["rows"] if row["crop_name"] == "Cauliflower")
    late_cauli = next(row for row in late["rows"] if row["crop_name"] == "Cauliflower")
    assert early_cauli["can_mature"] is True
    assert late_cauli["can_mature"] is False


def test_snapshot_budget_changes_affordability():
    affordable = build_filtered_snapshot(
        season="Summer",
        current_day=1,
        tiles=20,
        budget=5000,
        goal="profit_per_day",
        fertilizer="none",
    )
    over_budget = build_filtered_snapshot(
        season="Summer",
        current_day=1,
        tiles=20,
        budget=100,
        goal="profit_per_day",
        fertilizer="none",
    )

    affordable_melon = next(row for row in affordable["rows"] if row["crop_name"] == "Melon")
    over_budget_melon = next(row for row in over_budget["rows"] if row["crop_name"] == "Melon")
    assert affordable_melon["affordable"] is True
    assert over_budget_melon["affordable"] is False


def test_snapshot_invalid_inputs_are_handled():
    snapshot = build_filtered_snapshot(
        season="NotASeason",
        current_day="x",
        tiles="y",
        budget="oops",
        goal="unknown-goal",
        fertilizer="unknown-fertilizer",
    )

    assert snapshot["rows"]
    assert snapshot["filters"]["season"] == "Spring"
    assert snapshot["filters"]["current_day"] == 1
    assert snapshot["filters"]["tiles"] == 80
    assert snapshot["filters"]["goal"] == "profit_per_day"


def test_snapshot_excludes_profit_unsupported_rows():
    snapshot = build_filtered_snapshot(
        season="Spring",
        current_day=1,
        tiles=80,
        budget=5000,
        goal="profit_per_day",
        fertilizer="none",
    )

    assert snapshot["rows"]
    assert all(row.get("profit_supported", True) is True for row in snapshot["rows"])
