def load_excel(path, sheet_name=None):
    import pandas as pd
    return pd.read_excel(path, sheet_name=sheet_name)


def load_manual_csv(path):
    import pandas as pd
    return pd.read_csv(path)


def load_from_db(query, connection_string):
    import pandas as pd
    from sqlalchemy import create_engine
    engine = create_engine(connection_string)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def create_case_template(path, file_format="csv"):
    """Create a new case template file with required columns.

    Args:
        path (str): Output path for the template file.
        file_format (str): 'csv' or 'xlsx'.
    """
    import pandas as pd
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
    df = pd.DataFrame(columns=cols)
    if file_format == "xlsx" or str(path).lower().endswith(".xlsx"):
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, index=False)
    return path


def clean_and_validate_cases(df):
    """Clean and validate a dataframe of cases.

    Returns cleaned dataframe. Raises ValueError on fatal validation errors.
    """
    import pandas as pd

    required = [
        "date",
        "complainant",
        "accused",
        "offences",
        "subject",
        "court_heard_in",
        "submitted",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df2 = df.copy()
    # Normalize string columns
    for c in ["complainant", "accused", "offences", "subject", "court_heard_in", "submitted_documents"]:
        if c in df2.columns:
            df2[c] = df2[c].astype(object).where(pd.notna(df2[c]), None)
    # Parse dates (coerce invalids to NaT)
    for col in ["date", "last_court_date", "next_court_date"]:
        if col in df2.columns:
            df2[col] = pd.to_datetime(df2[col], errors="coerce")

    # submitted -> accept yes/no/true/false/1/0
    def normalize_submitted(v):
        if pd.isna(v):
            return 0
        s = str(v).strip().lower()
        return 1 if s in ("1", "true", "yes", "y") else 0

    df2["submitted"] = df2["submitted"].apply(normalize_submitted)

    # Check required non-empty fields per row
    errors = []
    for i, row in df2.iterrows():
        for c in required:
            if pd.isna(row.get(c)) or (isinstance(row.get(c), str) and row.get(c).strip() == ""):
                errors.append(f"Row {i}: required field '{c}' is empty")
    if errors:
        raise ValueError("Validation errors:\n" + "\n".join(errors))

    # Convert date columns to ISO strings for DB insertion (leave None as None)
    for col in ["date", "last_court_date", "next_court_date"]:
        if col in df2.columns:
            df2[col] = df2[col].dt.strftime("%Y-%m-%d")

    return df2


def import_template_into_db(path, db_path):
    """Read a CSV/XLSX template, validate it and insert rows into DB."""
    import pandas as pd
    from .storage import init_cases_table, insert_cases_from_df

    if str(path).lower().endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    cleandf = clean_and_validate_cases(df)
    init_cases_table(db_path)
    insert_cases_from_df(cleandf, db_path)
    return len(cleandf)
