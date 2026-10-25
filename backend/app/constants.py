"""Small shared lists so the backend and the API agree on allowed values."""

CATEGORIES = [
    "Pottery",
    "Textiles",
    "Jewellery",
    "Woodwork",
    "Paintings",
    "Metalcraft",
    "Leather",
    "Bamboo & Cane",
    "Home Decor",
]

# An order item moves forward through these steps (never backwards).
ITEM_STATUS_FLOW = ["placed", "packed", "shipped", "delivered"]

MAX_IMAGES_PER_PRODUCT = 5
