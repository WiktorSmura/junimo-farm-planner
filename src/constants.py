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

# Known per-harvest base yield overrides for crops that produce multiple items.
# Chance-based bonus drops are intentionally excluded from this deterministic baseline.
BASE_YIELD_OVERRIDES = {
    "Blueberry": 3,
    "Coffee Bean": 4,
    "Cranberries": 2,
}

# Data corrections for the default "Valley farm" context.
# The source dataset uses "Any" for several special crops that are location-gated in-game.
CROP_RULE_OVERRIDES = {
    "Ancient Fruit": {
        "valley_seasons": ("Spring", "Summer", "Fall"),
        "rule_note": "All-year growth applies in Greenhouse/Ginger Island, not standard outdoor winter.",
    },
    "Pineapple": {
        "valley_seasons": ("Summer",),
        "rule_note": "All-year growth applies on Ginger Island.",
    },
    "Taro Root (Irrigated)": {
        "valley_seasons": ("Summer",),
        "rule_note": "All-year growth applies on Ginger Island.",
    },
    "Taro Root (Unirrigated)": {
        "valley_seasons": ("Summer",),
        "rule_note": "All-year growth applies on Ginger Island.",
    },
    "Tea Leaves": {
        "valley_seasons": ("Spring", "Summer", "Fall"),
        "special_harvest_model": "last_week_daily",
        "rule_note": "Outdoor harvest occurs only during days 22-28 each season.",
    },
    "Qi Fruit": {
        "valley_seasons": ("Spring", "Summer", "Fall", "Winter"),
        "quest_only": True,
        "rule_note": "Only available during the Qi's Crop quest.",
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
