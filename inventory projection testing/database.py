from sqlalchemy import create_engine

DATABASE_NAME = "inventory.db"

engine = create_engine(f"sqlite:///{DATABASE_NAME}")