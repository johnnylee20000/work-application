import pandas as pd
import pytest
import os

from src.storage import init_cases_table, insert_cases_from_df, read_table_from_sqlite


def test_insert_and_read(tmp_path):
    db = tmp_path / "test.db"
    init_cases_table(str(db))
    data = {
        "date": ["2025-11-24"],
        "complainant": ["Alice"],
        "accused": ["Bob"],
        "offences": ["Theft"],
        "subject": ["Case A"],
        "court_heard_in": ["Magistrates Court"],
        "submitted": [1],
        "submitted_documents": ["doc1.pdf"],
        "last_court_date": ["2025-11-01"],
        "next_court_date": ["2025-12-01"],
    }
    df = pd.DataFrame(data)
    insert_cases_from_df(df, str(db))
    out = read_table_from_sqlite("cases", str(db))
    assert len(out) == 1
    assert out.loc[0, "complainant"] == "Alice"
    assert out.loc[0, "court_heard_in"] == "Magistrates Court"
