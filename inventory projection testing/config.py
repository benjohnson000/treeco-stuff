import json

from app_paths import APP_DIR

SETTINGS_FILE = APP_DIR / "settings.json"
REQUIRED_SETTINGS = (
    "stock_target_days",
    "vendor_lead_time_days",
    "buffer_days",
)


def load_settings(filename=SETTINGS_FILE):
    """Load and validate the reorder settings kept beside the application."""
    with open(filename, encoding="utf-8") as file:
        settings = json.load(file)

    return _validate_settings(settings)


def save_settings(settings, filename=SETTINGS_FILE):
    """Validate and persist settings selected in the dashboard."""
    validated_settings = _validate_settings(settings)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(validated_settings, file, indent=2)
        file.write("\n")


def _validate_settings(settings):
    validated_settings = {}

    for name in REQUIRED_SETTINGS:
        if name not in settings:
            raise ValueError(f"Missing required setting: {name}")
        if not isinstance(settings[name], (int, float)) or settings[name] < 0:
            raise ValueError(f"{name} must be a non-negative number")
        validated_settings[name] = settings[name]

    return validated_settings
