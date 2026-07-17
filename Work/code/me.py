from pathlib import Path

import pandas as pd


def load_dspace_csv(file_path: str | Path) -> pd.DataFrame:
    """
    Load a dSPACE CSV export containing:
    - a 'path' row with signal names
    - a 'trace_values' row followed by numerical samples
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    # Read the file without assuming where the header and data rows are.
    raw_df = pd.read_csv(
        file_path,
        header=None,
        dtype=str,
        keep_default_na=False
    )

    # Remove leading/trailing whitespace from every string cell.
    raw_df = raw_df.apply(lambda column: column.str.strip())

    # Find the row containing "path".
    path_rows = raw_df.index[
        raw_df.apply(
            lambda row: row.str.lower().eq("path").any(),
            axis=1
        )
    ]

    if path_rows.empty:
        raise ValueError("Could not find a row containing 'path'.")

    path_row_index = path_rows[0]

    # Find the row containing "trace_values".
    trace_rows = raw_df.index[
        raw_df.apply(
            lambda row: row.str.lower().eq("trace_values").any(),
            axis=1
        )
    ]

    if trace_rows.empty:
        raise ValueError("Could not find a row containing 'trace_values'.")

    trace_row_index = trace_rows[0]

    # Extract signal names from the path row.
    column_names = raw_df.iloc[path_row_index].tolist()

    # The first column normally contains the row identifier "path".
    column_names[0] = "Time"

    # Replace missing signal names with generated names.
    column_names = [
        name if name else f"Signal_{index}"
        for index, name in enumerate(column_names)
    ]

    # Ensure duplicate signal names do not cause ambiguity.
    seen_names: dict[str, int] = {}
    unique_column_names: list[str] = []

    for name in column_names:
        count = seen_names.get(name, 0)

        if count == 0:
            unique_name = name
        else:
            unique_name = f"{name}_{count}"

        unique_column_names.append(unique_name)
        seen_names[name] = count + 1

    # Numerical values may begin either on the trace_values row or the next row.
    data_df = raw_df.iloc[trace_row_index:].copy()
    data_df.columns = unique_column_names

    # Remove the trace_values label without replacing it with a fake time value.
    data_df.iloc[0, 0] = ""

    # Convert every value to numeric.
    # Invalid metadata cells become NaN.
    data_df = data_df.apply(
        lambda column: pd.to_numeric(column, errors="coerce")
    )

    # Remove rows that contain no numerical data.
    data_df = data_df.dropna(how="all")

    # A valid sample should normally have a time value.
    data_df = data_df.dropna(subset=["Time"])

    # Reset row numbering after removing metadata rows.
    data_df = data_df.reset_index(drop=True)

    return data_df


if __name__ == "__main__":
    file_path = "your_file.csv"

    try:
        data_df = load_dspace_csv(file_path)

        print(data_df.head())
        print("\nColumn types:")
        print(data_df.dtypes)

    except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
        print(f"Failed to load the dSPACE CSV: {error}")


