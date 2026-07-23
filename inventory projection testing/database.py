from datetime import datetime
from shutil import copy2

from sqlalchemy import create_engine

from app_paths import BACKUP_DIR, DATABASE_FILE, ensure_data_directories

ensure_data_directories()
engine = create_engine(f"sqlite:///{DATABASE_FILE.as_posix()}")


def replace_imported_data(inventory, usage):
    """Back up and replace the current multi-branch report snapshot in SQLite."""
    engine.dispose()
    if DATABASE_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        copy2(DATABASE_FILE, BACKUP_DIR / f"inventory_{timestamp}.db")
    inventory.to_sql("inventory", engine, if_exists="replace", index=False)
    usage.to_sql("usage_history", engine, if_exists="replace", index=False)
