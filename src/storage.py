def save_dataframe_to_sqlite(df, table_name, db_path, if_exists="append", index=False):
    from sqlalchemy import create_engine
    engine = create_engine(f"sqlite:///{db_path}")
    df.to_sql(table_name, engine, if_exists=if_exists, index=index)


def read_table_from_sqlite(table_name, db_path):
    from sqlalchemy import create_engine
    import pandas as pd
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        return pd.read_sql_table(table_name, conn)


def init_cases_table(db_path):
    """Create the `cases` table with the expected schema if it doesn't exist."""
    from sqlalchemy import create_engine, text
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY,
                date TEXT,
                complainant TEXT,
                accused TEXT,
                offences TEXT,
                subject TEXT,
                court_heard_in TEXT,
                submitted INTEGER,
                submitted_documents TEXT,
                last_court_date TEXT,
                next_court_date TEXT
            )
            """
        ))


def insert_cases_from_df(df, db_path):
    """Normalize a dataframe and append its rows to the `cases` table.

    - Normalizes date columns to ISO `YYYY-MM-DD` strings (where possible)
    - Converts `submitted` to 0/1
    """
    import pandas as pd
    from sqlalchemy import create_engine

    df2 = df.copy()
    # Ensure columns exist
    cols = [
        "date",
        "complainant",
        "accused",
        "offences",
        "subject",
        "court_heard_in",
        "submitted",
        "submitted_documents",
        "last_court_date",
        "next_court_date",
    ]
    for c in cols:
        if c not in df2.columns:
            df2[c] = None

    for col in ["date", "last_court_date", "next_court_date"]:
        df2[col] = pd.to_datetime(df2[col], errors="coerce").dt.strftime("%Y-%m-%d")

    def to_bool_flag(v):
        if pd.isna(v):
            return 0
        s = str(v).strip().lower()
        return 1 if s in ("1", "true", "yes", "y") else 0

    df2["submitted"] = df2["submitted"].apply(to_bool_flag)

    engine = create_engine(f"sqlite:///{db_path}")
    df2.to_sql("cases", engine, if_exists="append", index=False)
