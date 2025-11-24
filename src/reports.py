def generate_summary(df):
    import pandas as pd
    summary = df.describe(include='all')
    return summary


def save_summary_csv(df, out_path):
    df.to_csv(out_path)


def plot_numeric_histograms(df, out_path_prefix):
    import matplotlib.pyplot as plt
    numeric = df.select_dtypes(include='number')
    for col in numeric.columns:
        plt.figure()
        numeric[col].hist()
        plt.title(col)
        plt.savefig(f"{out_path_prefix}_{col}.png")
        plt.close()


def aggregate_cases_report(db_path, out_csv="cases_summary.csv", out_prefix="cases_report"):
    """Generate aggregated reports from the `cases` table.

    - Writes `out_csv` with counts by `court_heard_in` and by `offences` and submitted status.
    - Saves bar chart PNGs with `out_prefix`.
    Returns path to CSV and list of generated plot files.
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    from .storage import read_table_from_sqlite

    try:
        df = read_table_from_sqlite("cases", db_path)
    except Exception:
        # If table doesn't exist, return empty
        df = pd.DataFrame()

    reports = {}
    plots = []

    if df.empty:
        df_out = pd.DataFrame({"message": ["no data"]})
        df_out.to_csv(out_csv, index=False)
        return out_csv, plots

    # Counts by court
    court_counts = df.groupby("court_heard_in").size().reset_index(name="count").sort_values("count", ascending=False)
    court_counts.to_csv(f"{out_prefix}_by_court.csv", index=False)
    reports["by_court"] = f"{out_prefix}_by_court.csv"

    # Plot counts by court
    plt.figure(figsize=(8,6))
    plt.bar(court_counts["court_heard_in"].astype(str), court_counts["count"])
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Count")
    plt.title("Cases by Court")
    court_plot = f"{out_prefix}_by_court.png"
    plt.tight_layout()
    plt.savefig(court_plot)
    plt.close()
    plots.append(court_plot)

    # Submitted vs unsubmitted by court (pivot)
    df["submitted_flag"] = df["submitted"].fillna(0).astype(int)
    pivot = df.pivot_table(index="court_heard_in", columns="submitted_flag", values="date", aggfunc="count", fill_value=0)
    pivot.to_csv(f"{out_prefix}_submitted_by_court.csv")
    reports["submitted_by_court"] = f"{out_prefix}_submitted_by_court.csv"

    # Plot stacked bar
    try:
        pivot.plot(kind="bar", stacked=True, figsize=(8,6))
        plt.ylabel("Count")
        plt.title("Submitted vs Unsubmitted by Court")
        plt.xticks(rotation=45, ha='right')
        stacked_plot = f"{out_prefix}_submitted_by_court.png"
        plt.tight_layout()
        plt.savefig(stacked_plot)
        plt.close()
        plots.append(stacked_plot)
    except Exception:
        pass

    # Overall summary CSV
    overall = pd.DataFrame({
        "total_cases": [len(df)],
        "unique_courts": [df["court_heard_in"].nunique()],
        "submitted_count": [int(df["submitted"].fillna(0).astype(int).sum())]
    })
    overall.to_csv(out_csv, index=False)

    return out_csv, plots
