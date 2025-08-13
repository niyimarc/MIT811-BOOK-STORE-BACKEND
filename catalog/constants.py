PRODUCT_STATUS = (
    ("Publish", "Publish"),
    ("Draft", "Draft")
)

PHYSICAL_STOCK_STATUS = [
    ("in_stock", "In Stock"),
    ("low_stock", "Low Stock"),
    ("out_of_stock", "Out of Stock"),
    ("pre_order", "Pre-Order"),
    ("backorder", "Backorder"),
    ("out_of_print", "Out of Print"),
    ("print_on_demand", "Print on Demand"),
]

EBOOK_STOCK_STATUS = [
    ("available", "Available"),
    ("unavailable", "Unavailable"),
    ("pre_order", "Pre-Order"),
]

BOOK_FORMAT_CHOICES = [
    ("physical", "Physical"),
    ("ebook", "E-Book"),
    ("both", "Both"),
]

BOOK_LANGUAGES = [
    ("en", "English"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("zh", "Chinese"),
    ("jp", "Japanese"),
]
