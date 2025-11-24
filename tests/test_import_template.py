import pandas as pd
import pytest
from pathlib import Path
from src.collectors import import_template_into_db
from src.storage import read_table_from_sqlite


def test_import_template_csv(tmp_path):
    db = tmp_path / "test.db"
    csv = tmp_path / "filled.csv"
    data = {
        "date": ["2025-11-24"],
        "complainant": ["Alice"],
        "accused": ["Bob"],
        "offences": ["Theft"],
        "subject": ["Case A"],
        "court_heard_in": ["Magistrates Court"],
        "submitted": ["yes"],
        "submitted_documents": ["doc1.pdf"],
        "last_court_date": ["2025-11-01"],
        "next_court_date": ["2025-12-01"],
    }
    pd.DataFrame(data).to_csv(csv, index=False)
    count = import_template_into_db(str(csv), str(db))
    assert count == 1
    out = read_table_from_sqlite("cases", str(db))
    assert len(out) == 1
    assert out.loc[0, "complainant"] == "Alice"
