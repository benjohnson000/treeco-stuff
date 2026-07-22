from pathlib import Path


VENDORS_FILE = Path(__file__).parent / "data" / "vendors.txt"


def load_vendors(filename=VENDORS_FILE):
    """Load vendor names from a plain text file, one vendor per line."""
    path = Path(filename)
    if not path.exists():
        return []

    vendors = []
    with open(path, encoding="utf-8") as file:
        for line in file:
            vendor = line.strip()
            if vendor and not vendor.startswith("#"):
                vendors.append(vendor)

    return sorted(vendors, key=len, reverse=True)


def find_vendor(description, vendors):
    """Return the first vendor name found in an item description."""
    if not isinstance(description, str):
        return None

    normalized_description = description.casefold()
    for vendor in vendors:
        if vendor.casefold() in normalized_description:
            return vendor

    return None
