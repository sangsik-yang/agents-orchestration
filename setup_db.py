import argparse
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional

from config import get_titanic_db_path

DEFAULT_TITANIC_CSV_URL = (
    "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
)
DEFAULT_TABLE_NAME = "titanic"


def clean_titanic_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the Titanic dataset before loading it into SQLite."""
    cleaned = df.copy()
    cleaned["Age"] = cleaned["Age"].fillna(cleaned["Age"].median())
    cleaned = cleaned.drop(columns=["Cabin"])
    cleaned["Embarked"] = cleaned["Embarked"].fillna(cleaned["Embarked"].mode()[0])
    cleaned.columns = [column.lower() for column in cleaned.columns]
    return cleaned


def setup_database(
    csv_url: str = DEFAULT_TITANIC_CSV_URL,
    db_path: Optional[Path] = None,
    table_name: str = DEFAULT_TABLE_NAME,
) -> None:
    """Download, clean and load Titanic data into SQLite."""
    print(f"Downloading Titanic dataset from {csv_url}...")

    df = clean_titanic_data(pd.read_csv(csv_url))
    resolved_db_path = db_path or get_titanic_db_path()
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(resolved_db_path) as conn:
        print(f"Loading data into '{table_name}' table in '{resolved_db_path}'...")
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    print("Database setup complete.")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Create a SQLite Titanic dataset database.")
    parser.add_argument(
        "--csv-url",
        default=DEFAULT_TITANIC_CSV_URL,
        help="CSV URL or local CSV path to load.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Output SQLite database path. Defaults to TITANIC_DB_PATH or titanic.db.",
    )
    parser.add_argument(
        "--table-name",
        default=DEFAULT_TABLE_NAME,
        help="SQLite table name to replace or create.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        setup_database(
            csv_url=args.csv_url,
            db_path=args.db_path,
            table_name=args.table_name,
        )
    except Exception as e:
        print(f"Error setting up database: {type(e).__name__}: {e}")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
