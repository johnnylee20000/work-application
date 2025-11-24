import pandas as pd
import pytest

from src.collectors import clean_and_validate_cases, create_case_template


def test_clean_and_validate_ok(tmp_path):
    data = {
        "date": ["2025-11-24"],
        "complainant": ["Alice"],
        "accused": ["Bob"],
        "offences": ["Theft"],
        "subject": ["Case A"],
        "court_heard_in": ["Magistrates Court"],
        "submitted": ["yes"],
    }
    df = pd.DataFrame(data)
    cleaned = clean_and_validate_cases(df)
    assert cleaned.loc[0, "complainant"] == "Alice"
    assert cleaned.loc[0, "submitted"] == 1
    assert cleaned.loc[0, "date"] == "2025-11-24"


def test_clean_and_validate_missing_required():
    data = {
        "date": ["2025-11-24"],
        "complainant": ["Alice"],
        # missing accused
        "offences": ["Theft"],
        "subject": ["Case A"],
        "court_heard_in": ["Magistrates Court"],
        "submitted": ["yes"],
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError):
        clean_and_validate_cases(df)


def test_create_case_template_file(tmp_path):
    p = tmp_path / "template.csv"
    create_case_template(str(p))
    df = pd.read_csv(p)
    # columns should include court_heard_in
    assert "court_heard_in" in df.columns
