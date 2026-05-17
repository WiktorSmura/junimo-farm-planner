from __future__ import annotations

import math
from typing import Any

from .constants import CROP_PROCESSING_CATEGORIES

MINUTES_PER_DAY = 1600
ARTISAN_MULTIPLIER = 1.4

RAW_METHOD_ID = "raw"
EQUIPMENT_NONE = "none"
EQUIPMENT_KEG = "keg"
EQUIPMENT_PRESERVES_JAR = "preserves_jar"
EQUIPMENT_MILL = "mill"
EQUIPMENT_OIL_MAKER = "oil_maker"


def build_processing_methods(crop_name: str, base_price: float, artisan: bool = False) -> list[dict[str, Any]]:
    base_price = max(0.0, float(base_price))
    methods = [_method("raw", "Raw Sale", crop_name, EQUIPMENT_NONE, 1, base_price, 0, False)]
    category = CROP_PROCESSING_CATEGORIES.get(crop_name, "unsupported")

    if crop_name == "Coffee Bean":
        methods.append(_method("keg_coffee", "Keg", "Coffee", EQUIPMENT_KEG, 5, 150, 120, False))
        return methods

    if crop_name == "Hops":
        methods.append(_method("keg_pale_ale", "Keg", "Pale Ale", EQUIPMENT_KEG, 1, 300, 2250, True, artisan))
    elif crop_name == "Wheat":
        methods.append(_method("keg_beer", "Keg", "Beer", EQUIPMENT_KEG, 1, 200, 1750, True, artisan))
        methods.append(_method("mill_flour", "Mill", "Wheat Flour", EQUIPMENT_MILL, 1, 50, MINUTES_PER_DAY, False))
    elif crop_name == "Tea Leaves":
        methods.append(_method("keg_green_tea", "Keg", "Green Tea", EQUIPMENT_KEG, 1, 100, 180, True, artisan))
    elif crop_name == "Beet":
        methods.append(_method("mill_sugar", "Mill", "Sugar", EQUIPMENT_MILL, 1, 150, MINUTES_PER_DAY, False))
    elif crop_name.startswith("Unmilled Rice"):
        methods.append(_method("mill_rice", "Mill", "Rice", EQUIPMENT_MILL, 1, 100, MINUTES_PER_DAY, False))
    elif crop_name == "Corn":
        methods.append(_method("oil", "Oil Maker", "Oil", EQUIPMENT_OIL_MAKER, 1, 100, 1000, False))
    elif crop_name == "Sunflower":
        methods.append(_method("oil", "Oil Maker", "Oil", EQUIPMENT_OIL_MAKER, 1, 100, 60, False))

    if category == "fruit":
        methods.append(
            _method(
                "preserves_jelly",
                "Preserves Jar",
                "Jelly",
                EQUIPMENT_PRESERVES_JAR,
                1,
                (2 * base_price) + 50,
                4000,
                True,
                artisan,
            )
        )
        methods.append(_method("keg_wine", "Keg", "Wine", EQUIPMENT_KEG, 1, 3 * base_price, 10000, True, artisan))
    elif category == "vegetable":
        methods.append(
            _method(
                "preserves_pickles",
                "Preserves Jar",
                "Pickles",
                EQUIPMENT_PRESERVES_JAR,
                1,
                (2 * base_price) + 50,
                4000,
                True,
                artisan,
            )
        )
        methods.append(
            _method(
                "keg_juice",
                "Keg",
                "Juice",
                EQUIPMENT_KEG,
                1,
                math.floor(2.25 * base_price),
                6000,
                True,
                artisan,
            )
        )

    return _deduplicate_methods(methods)


def best_processed_unit_price(crop_name: str, base_price: float, artisan: bool = False) -> float:
    return max(method["value_per_input"] for method in build_processing_methods(crop_name, base_price, artisan=artisan))


def method_by_id(crop_name: str, base_price: float, method_id: str, artisan: bool = False) -> dict[str, Any] | None:
    for method in build_processing_methods(crop_name, base_price, artisan=artisan):
        if method["method_id"] == method_id:
            return method
    return None


def evaluate_processing_capacity(
    method: dict[str, Any],
    raw_units: float,
    raw_unit_price: float,
    machine_count: int,
    horizon_days: int,
) -> dict[str, Any]:
    raw_units = max(0.0, float(raw_units))
    raw_unit_price = max(0.0, float(raw_unit_price))
    machine_count = max(0, int(machine_count))
    horizon_days = max(0, int(horizon_days))
    input_units = max(1, int(method["input_units"]))

    possible_batches = math.floor(raw_units / input_units)
    if method["equipment"] == EQUIPMENT_NONE:
        machine_cycles = possible_batches
        processed_batches = 0
    elif method["equipment"] == EQUIPMENT_MILL:
        machine_cycles = possible_batches if machine_count > 0 else 0
        processed_batches = min(possible_batches, machine_cycles)
    elif method["processing_minutes"] > 0:
        machine_cycles = math.floor((horizon_days * MINUTES_PER_DAY) / int(method["processing_minutes"])) * machine_count
        processed_batches = min(possible_batches, machine_cycles)
    else:
        machine_cycles = 0
        processed_batches = 0

    processed_units = processed_batches * input_units
    leftover_units = max(0.0, raw_units - processed_units)
    processed_revenue = processed_batches * float(method["batch_value"])
    raw_revenue = raw_units * raw_unit_price if method["equipment"] == EQUIPMENT_NONE else leftover_units * raw_unit_price
    total_revenue = processed_revenue + raw_revenue

    return {
        "method_id": method["method_id"],
        "method_name": method["method_name"],
        "product_name": method["product_name"],
        "equipment": method["equipment"],
        "raw_units": raw_units,
        "machine_cycles": machine_cycles,
        "processed_batches": processed_batches,
        "processed_units": processed_units,
        "leftover_units": leftover_units,
        "processed_revenue": processed_revenue,
        "raw_revenue": raw_revenue,
        "total_revenue": total_revenue,
        "extra_revenue": total_revenue - (raw_units * raw_unit_price),
        "unit_value": method["value_per_input"],
        "input_units": input_units,
        "processing_minutes": method["processing_minutes"],
        "artisan_applied": method["artisan_applied"],
    }


def _method(
    method_id: str,
    method_name: str,
    product_name: str,
    equipment: str,
    input_units: int,
    batch_value: float,
    processing_minutes: int,
    artisan_eligible: bool,
    artisan: bool = False,
) -> dict[str, Any]:
    adjusted_batch_value = float(batch_value)
    artisan_applied = artisan_eligible and artisan
    if artisan_applied:
        adjusted_batch_value = math.floor(adjusted_batch_value * ARTISAN_MULTIPLIER)

    return {
        "method_id": method_id,
        "method_name": method_name,
        "product_name": product_name,
        "equipment": equipment,
        "input_units": input_units,
        "batch_value": adjusted_batch_value,
        "value_per_input": adjusted_batch_value / input_units,
        "processing_minutes": processing_minutes,
        "artisan_eligible": artisan_eligible,
        "artisan_applied": artisan_applied,
    }


def _deduplicate_methods(methods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated = {}
    for method in methods:
        deduplicated[method["method_id"]] = method
    return list(deduplicated.values())
