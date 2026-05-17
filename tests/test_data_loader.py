from pathlib import Path

from src.data_loader import clean_crops, load_clean_crops, load_raw_crops


def test_load_raw_crops_uses_canonical_dataset():
    raw = load_raw_crops()

    assert len(raw) == 54
    assert {"crop_name", "season", "seed_price", "sell_price"} <= set(raw.columns)


def test_clean_crops_merges_duplicate_seasons():
    clean = clean_crops(load_raw_crops())

    assert len(clean) == 50
    assert clean["crop_id"].is_unique

    corn = clean.loc[clean["crop_name"] == "Corn"].iloc[0]
    assert corn["seasons_list"] == ["Summer", "Fall"]
    assert corn["season"] == "Summer/Fall"
    assert bool(corn["is_multi_season"]) is True

    green_bean = clean.loc[clean["crop_name"] == "Green Bean"].iloc[0]
    assert bool(green_bean["is_trellis"]) is True


def test_clean_crops_applies_game_rule_overrides():
    clean = clean_crops(load_raw_crops())

    ancient = clean.loc[clean["crop_name"] == "Ancient Fruit"].iloc[0]
    assert ancient["seasons_list"] == ["Spring", "Summer", "Fall"]
    assert ancient["available_days"] == 84
    assert ancient["first_harvest_day"] == 29
    assert bool(ancient["will_mature"]) is True

    coffee = clean.loc[clean["crop_name"] == "Coffee Bean"].iloc[0]
    assert coffee["seasons_list"] == ["Spring", "Summer"]
    assert coffee["base_yield"] == 4
    assert coffee["max_harvests"] == 23

    tea = clean.loc[clean["crop_name"] == "Tea Leaves"].iloc[0]
    assert tea["seasons_list"] == ["Spring", "Summer", "Fall"]
    assert tea["max_harvests"] == 21

    qi = clean.loc[clean["crop_name"] == "Qi Fruit"].iloc[0]
    assert bool(qi["is_quest_only"]) is True


def test_load_clean_crops_reads_or_builds_processed_cache():
    clean = load_clean_crops(force_refresh=True)
    processed_file = Path("data/processed/crops_clean.csv")

    assert processed_file.exists()
    assert len(clean) == 50
    assert "seasons_list" in clean.columns
