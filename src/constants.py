from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SPECIFICATION_DIR = PROJECT_ROOT / "specification"

RAW_CROPS_FILE = RAW_DATA_DIR / "stardew_crops_raw.csv"
CLEAN_CROPS_FILE = PROCESSED_DATA_DIR / "crops_clean.csv"

SEASON_ORDER = ("Spring", "Summer", "Fall", "Winter")
SEASON_LENGTH_DAYS = 28

TRELLIS_CROPS = frozenset(
    {
        "Grape",
        "Green Bean",
        "Hops",
    }
)

RAW_CROP_SOURCE_FILES = (
    "spring_crops_info.csv",
    "summer_crops_info.csv",
    "fall_crops_info.csv",
    "winter_crops_info.csv",
    "special_crops_info.csv",
)

# Manual additions for crops missing from the Kaggle source file.
# Broccoli was added in Stardew Valley 1.6 and is present on the current wiki,
# but is absent from the uploaded raw file.
MANUAL_RAW_CROP_ROWS = (
    {
        "crop_name": "Broccoli",
        "description": "The flowering head of a broccoli plant. The tiny buds give it a unique texture.",
        "days_to_grow": 8,
        "regrowth": 4,
        # Broccoli Seeds are not sold in shops; this is the seed sell price/opportunity cost.
        "seed_price": 40,
        "sell_price": 70,
        "multiple_harvests": "YES",
        "edible": "YES",
        "season": "Fall",
    },
)

# Numeric corrections applied after loading raw data.
# These keep the dashboard closer to current Stardew Valley 1.6 mechanics.
CROP_NUMERIC_OVERRIDES = {
    # 1.6 seasonal seeds are not sold by Pierre/Joja/Traveling Cart; use seed sell price
    # as an opportunity-cost model instead of the crop sell price from the raw source.
    "Carrot": {"seed_price": 15},
    "Summer Squash": {"seed_price": 20},
    "Broccoli": {"seed_price": 40},
    "Powdermelon": {"seed_price": 20},
    # Coffee Bean can be planted directly. For repeat planting, the relevant opportunity
    # cost is one bean, not a normal shop seed price.
    "Coffee Bean": {"seed_price": 15},
    # Ancient Seeds are crafted from the artifact recipe or obtained by seed maker;
    # they are not a regular gold shop seed.
    "Ancient Fruit": {"seed_price": 0},
    # Fiber Seeds are crafted. The source used 5g, but the current wiki lists crafting recipe.
    "Fiber Seeds": {"seed_price": 0},
    # The uploaded raw source has Pineapple as one-shot, but current game data regrows it.
    "Pineapple": {"regrowth": 7},
}

# Guaranteed per-harvest yields. This is deterministic output before rare random extras.
BASE_YIELD_OVERRIDES = {
    "Blueberry": 3,
    "Coffee Bean": 4,
    "Cranberries": 2,
}

# Expected bonus yield used for profit estimates when the wiki gives a useful expectation.
# Rare "chance for more" outcomes are otherwise intentionally documented but excluded from
# expected profit because the official crop table generally excludes them.
EXPECTED_EXTRA_YIELD_OVERRIDES = {
    "Potato": 0.25,
    "Cranberries": 0.11,
    # Fiber produces 4-7 fiber; use midpoint for expected raw-material yield.
    "Fiber Seeds": 4.5,  # base 1 + 4.5 = 5.5 expected Fiber
}

RANDOM_EXTRA_YIELD_NOTES = {
    "Blueberry": "Guaranteed 3 blueberries; rare 2% extra not included in default expected yield.",
    "Coffee Bean": "Guaranteed 4 beans; rare 2% extra not included in default expected yield.",
    "Strawberry": "Rare 2% extra strawberries not included in default expected yield.",
    "Hot Pepper": "Rare 3% extra peppers not included in default expected yield.",
    "Tomato": "Rare 5% extra tomatoes not included in default expected yield.",
    "Eggplant": "Rare 0.2% extra eggplants not included in default expected yield.",
    "Cranberries": "Guaranteed 2 berries plus 0.11 expected extra berries per harvest.",
    "Potato": "Uses 1.25 expected potatoes per harvest, matching the wiki's high-probability potato exception.",
    "Fiber Seeds": "Uses midpoint of 4-7 Fiber per harvest; rare 1% extra Fiber not included.",
}

# Data corrections for the default "Valley farm" context.
# The source dataset uses "Any" for several special crops that are location-gated in-game.
CROP_RULE_OVERRIDES = {
    "Ancient Fruit": {
        "valley_seasons": ("Spring", "Summer", "Fall"),
        "farm_context": "standard_outdoor",
        "seed_price_model": "crafted_or_seed_maker",
        "rule_note": "Grows outdoors in Spring/Summer/Fall; all-year growth applies in Greenhouse/Ginger Island.",
    },
    "Cactus Fruit": {
        "farm_context": "greenhouse_indoor_or_island_only",
        "seed_price_model": "shop_gold",
        "rule_note": "Can only be grown in the Greenhouse, Garden Pots indoors, or on Ginger Island.",
    },
    "Pineapple": {
        "valley_seasons": ("Summer",),
        "farm_context": "standard_outdoor_or_ginger_island",
        "seed_price_model": "barter_or_seed_maker",
        "rule_note": "Grows in Summer on the standard farm and all year on Ginger Island; regrows every 7 days.",
    },
    "Taro Root (Irrigated)": {
        "valley_seasons": ("Summer",),
        "farm_context": "standard_outdoor_or_ginger_island",
        "seed_price_model": "barter_or_seed_maker",
        "rule_note": "Grows in Summer on the standard farm and all year on Ginger Island; irrigated growth model.",
    },
    "Taro Root (Unirrigated)": {
        "valley_seasons": ("Summer",),
        "farm_context": "standard_outdoor_or_ginger_island",
        "seed_price_model": "barter_or_seed_maker",
        "rule_note": "Grows in Summer on the standard farm and all year on Ginger Island; unirrigated growth model.",
    },
    "Tea Leaves": {
        "valley_seasons": ("Spring", "Summer", "Fall"),
        "farm_context": "standard_outdoor_or_indoor",
        "special_harvest_model": "last_week_daily",
        "seed_price_model": "tea_sapling",
        "rule_note": "Tea Bushes produce daily only during days 22-28 of Spring/Summer/Fall outdoors; Winter only if indoors.",
    },
    "Qi Fruit": {
        "valley_seasons": ("Spring", "Summer", "Fall", "Winter"),
        "farm_context": "quest_only",
        "quest_only": True,
        "seed_price_model": "quest_drop",
        "rule_note": "Only available during the Qi's Crop quest.",
    },
    "Mixed Seeds": {
        "valley_seasons": ("Spring", "Summer", "Fall"),
        "farm_context": "random_seed",
        "profit_supported": False,
        "seed_price_model": "random_drop",
        "rule_note": "Random seasonal output; exclude from deterministic profit rankings.",
    },
    "Mixed Flower Seeds": {
        "valley_seasons": ("Spring", "Summer", "Fall"),
        "farm_context": "random_seed",
        "profit_supported": False,
        "seed_price_model": "random_drop",
        "rule_note": "Random seasonal flower output; exclude from deterministic profit rankings.",
    },
    "Fiber Seeds": {
        "farm_context": "crafting_material",
        "seed_price_model": "crafted",
        "rule_note": "Useful for Fiber, not primarily a cash crop; expected yield uses midpoint of 4-7 Fiber.",
    },
    "Carrot": {
        "seed_price_model": "found_seed_opportunity_cost",
        "rule_note": "Seeds are not sold in shops; seed_price uses seed sell price/opportunity cost.",
    },
    "Summer Squash": {
        "seed_price_model": "found_seed_opportunity_cost",
        "rule_note": "Seeds are not sold in shops; seed_price uses seed sell price/opportunity cost.",
    },
    "Broccoli": {
        "seed_price_model": "found_seed_opportunity_cost",
        "rule_note": "Seeds are not sold in shops; seed_price uses seed sell price/opportunity cost.",
    },
    "Powdermelon": {
        "seed_price_model": "found_seed_opportunity_cost",
        "rule_note": "Seeds are not sold in shops; seed_price uses seed sell price/opportunity cost.",
    },
    "Coffee Bean": {
        "seed_price_model": "bean_opportunity_cost",
        "rule_note": (
            "Uses one Coffee Bean's sell price as seed opportunity cost; Traveling Cart initial purchase is much higher."
        ),
    },
    "Sunflower": {
        "rule_note": "Harvest can return Sunflower Seeds; this deterministic profit model does not credit seed returns.",
    },
}

# Processing categories are curated because the source crop data does not include
# Stardew item categories. Keep this limited to crops present in the dataset.
CROP_PROCESSING_CATEGORIES = {
    "Ancient Fruit": "fruit",
    "Blueberry": "fruit",
    "Cactus Fruit": "fruit",
    "Coffee Bean": "special",
    "Cranberries": "fruit",
    "Grape": "fruit",
    "Hot Pepper": "fruit",
    "Melon": "fruit",
    "Pineapple": "fruit",
    "Powdermelon": "fruit",
    "Qi Fruit": "fruit",
    "Rhubarb": "fruit",
    "Starfruit": "fruit",
    "Strawberry": "fruit",
    "Amaranth": "vegetable",
    "Artichoke": "vegetable",
    "Beet": "vegetable",
    "Bok Choy": "vegetable",
    "Broccoli": "vegetable",
    "Carrot": "vegetable",
    "Cauliflower": "vegetable",
    "Corn": "vegetable",
    "Eggplant": "vegetable",
    "Garlic": "vegetable",
    "Green Bean": "vegetable",
    "Hops": "vegetable",
    "Kale": "vegetable",
    "Parsnip": "vegetable",
    "Potato": "vegetable",
    "Pumpkin": "vegetable",
    "Radish": "vegetable",
    "Red Cabbage": "vegetable",
    "Summer Squash": "vegetable",
    "Taro Root (Irrigated)": "vegetable",
    "Taro Root (Unirrigated)": "vegetable",
    "Tea Leaves": "vegetable",
    "Tomato": "vegetable",
    "Unmilled Rice (Irrigated)": "vegetable",
    "Unmilled Rice (Unirrigated)": "vegetable",
    "Wheat": "vegetable",
    "Yam": "vegetable",
    "Blue Jazz": "unsupported",
    "Fairy Rose": "unsupported",
    "Fiber Seeds": "unsupported",
    "Mixed Flower Seeds": "unsupported",
    "Mixed Seeds": "unsupported",
    "Poppy": "unsupported",
    "Summer Spangle": "unsupported",
    "Sunflower": "unsupported",
    "Sweet Gem Berry": "unsupported",
    "Tulip": "unsupported",
}
