import json
from pathlib import Path


BRANCHES_FILE = Path(__file__).parent / "data" / "branches.json"


def load_branches(filename=BRANCHES_FILE):
    """Return configured Spruce branch IDs and display names."""
    with open(filename, encoding="utf-8") as file:
        branches = json.load(file)

    if not isinstance(branches, dict) or not branches:
        raise ValueError("branches.json must contain at least one branch ID and name.")

    return {str(branch_id): str(name) for branch_id, name in branches.items()}
