import pytest

from src.processing_math import build_processing_methods, evaluate_processing_capacity, method_by_id


def _method(crop_name: str, base_price: float, method_id: str, artisan: bool = False):
    method = method_by_id(crop_name, base_price, method_id, artisan=artisan)
    assert method is not None
    return method


def test_fruit_wine_and_jelly_values_with_artisan():
    wine = _method("Starfruit", 750, "keg_wine")
    artisan_wine = _method("Starfruit", 750, "keg_wine", artisan=True)
    jelly = _method("Blueberry", 50, "preserves_jelly")
    artisan_jelly = _method("Blueberry", 50, "preserves_jelly", artisan=True)

    assert wine["batch_value"] == 2250
    assert artisan_wine["batch_value"] == 3150
    assert jelly["batch_value"] == 150
    assert artisan_jelly["batch_value"] == 210


def test_vegetable_keg_and_jar_values():
    juice = _method("Pumpkin", 320, "keg_juice")
    pickles = _method("Pumpkin", 320, "preserves_pickles")
    amaranth_juice = _method("Amaranth", 150, "keg_juice")

    assert juice["batch_value"] == 720
    assert pickles["batch_value"] == 690
    assert amaranth_juice["batch_value"] == 337


def test_special_keg_outputs_and_artisan_rules():
    hops = _method("Hops", 25, "keg_pale_ale", artisan=True)
    coffee = _method("Coffee Bean", 15, "keg_coffee", artisan=True)
    tea = _method("Tea Leaves", 50, "keg_green_tea", artisan=True)
    tea_pickles = _method("Tea Leaves", 50, "preserves_pickles", artisan=True)

    assert hops["batch_value"] == 420
    assert coffee["batch_value"] == 150
    assert coffee["value_per_input"] == 30
    assert tea["batch_value"] == 140
    assert tea_pickles["batch_value"] == 210


def test_mill_and_oil_outputs():
    assert _method("Wheat", 25, "keg_beer")["batch_value"] == 200
    assert _method("Wheat", 25, "mill_flour")["batch_value"] == 50
    assert _method("Beet", 100, "mill_sugar")["batch_value"] == 150
    assert _method("Unmilled Rice (Irrigated)", 30, "mill_rice")["batch_value"] == 100
    assert _method("Corn", 50, "oil", artisan=True)["batch_value"] == 100
    assert _method("Sunflower", 80, "oil", artisan=True)["batch_value"] == 100


def test_sweet_gem_berry_is_raw_only():
    methods = build_processing_methods("Sweet Gem Berry", 3000, artisan=True)

    assert [method["method_id"] for method in methods] == ["raw"]


def test_capacity_with_zero_machines_leaves_all_units_raw():
    method = _method("Starfruit", 750, "keg_wine")

    result = evaluate_processing_capacity(
        method=method,
        raw_units=10,
        raw_unit_price=750,
        machine_count=0,
        horizon_days=28,
    )

    assert result["processed_units"] == 0
    assert result["leftover_units"] == 10
    assert result["total_revenue"] == 7500


def test_capacity_limited_by_machine_cycles_and_includes_leftover_raw():
    method = _method("Starfruit", 750, "keg_wine")

    result = evaluate_processing_capacity(
        method=method,
        raw_units=10,
        raw_unit_price=750,
        machine_count=1,
        horizon_days=7,
    )

    assert result["machine_cycles"] == 1
    assert result["processed_units"] == 1
    assert result["leftover_units"] == 9
    assert result["total_revenue"] == pytest.approx(2250 + (9 * 750))
