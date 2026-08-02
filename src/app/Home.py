from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app.column_mapper import (  # noqa: E402
    NO_COLUMN_OPTION,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    STANDARD_COLUMNS,
    apply_column_mapping,
    build_default_mapping,
    read_uploaded_columns,
    read_uploaded_dataframe,
    validate_mapping,
)
from src.data.cleaning import clean_pipeline  # noqa: E402
from src.visualization.rfm_dashboard import render_dashboard  # noqa: E402


def main() -> None:
    st.set_page_config(
        page_title="Customer Segmentation",
        page_icon=":bar_chart:",
        layout="wide",
    )

    page = st.sidebar.radio(
        "Pipeline page",
        ("Upload & Column Mapping", "RFM Dashboard"),
    )
    if page == "RFM Dashboard":
        render_dashboard()
        return

    render_upload_mapping()


def render_upload_mapping() -> None:
    st.title("Upload & Column Mapping")
    st.caption(
        "Accepted files: CSV or XLSX. Excel files with multiple sheets will be merged. "
        "Required mappings: InvoiceNo, StockCode, Quantity, InvoiceDate, UnitPrice, CustomerID. "
        "Optional mappings: Description, Country."
    )

    uploaded_file = st.file_uploader(
        "Upload transaction file (.csv or .xlsx)",
        type=["csv", "xlsx"],
        accept_multiple_files=False,
        help=(
            "The file can use Online Retail II column names or custom names. "
            "You must map all required columns before processing."
        ),
    )

    if uploaded_file is None:
        st.info("Upload a CSV or XLSX file to start.")
        return

    try:
        source_columns = read_uploaded_columns(uploaded_file, uploaded_file.name)
    except Exception as error:
        st.error(f"Cannot read file header: {error}")
        return

    if not source_columns:
        st.error("No columns were found in this file.")
        return

    default_mapping = build_default_mapping(source_columns)
    mapping = render_mapping_controls(source_columns, default_mapping, uploaded_file)
    validation = validate_mapping(mapping, source_columns)

    left, right = st.columns([1, 2])
    with left:
        st.subheader("Source columns")
        st.dataframe(
            pd.DataFrame({"Column": source_columns}),
            hide_index=True,
            use_container_width=True,
        )

    with right:
        st.subheader("Mapping status")
        if validation.is_valid:
            st.success("Mapping is valid.")
        else:
            for message in validation.messages():
                st.error(message)

        run_cleaning = st.button(
            "Apply mapping and clean data",
            type="primary",
            disabled=not validation.is_valid,
        )

    if not run_cleaning:
        return

    try:
        raw_df = read_uploaded_dataframe(uploaded_file, uploaded_file.name)
        mapped_df = apply_column_mapping(raw_df, mapping)

        with redirect_stdout(io.StringIO()):
            cleaned_df = clean_pipeline(mapped_df.copy())
    except Exception as error:
        st.error(f"Cannot process file: {error}")
        return

    st.success(
        f"Processed {len(raw_df):,} rows from {uploaded_file.name}."
    )

    preview_left, preview_right = st.columns(2)
    with preview_left:
        st.subheader("Mapped data preview")
        st.dataframe(mapped_df.head(20), use_container_width=True)

    with preview_right:
        st.subheader("Cleaned data preview")
        st.dataframe(cleaned_df.head(20), use_container_width=True)

    st.download_button(
        "Download cleaned CSV",
        data=cleaned_df.to_csv(index=False).encode("utf-8"),
        file_name="cleaned_transactions.csv",
        mime="text/csv",
    )


def render_mapping_controls(
    source_columns: list[str],
    default_mapping: dict[str, str | None],
    uploaded_file,
) -> dict[str, str | None]:
    st.subheader("Column mapping")
    st.caption(
        "Required: "
        + ", ".join(REQUIRED_COLUMNS)
        + ". Optional: "
        + ", ".join(OPTIONAL_COLUMNS)
        + "."
    )

    options = [NO_COLUMN_OPTION] + source_columns
    file_key = f"{uploaded_file.name}_{getattr(uploaded_file, 'size', 0)}"
    mapping: dict[str, str | None] = {}

    for standard_column in STANDARD_COLUMNS:
        default_source = default_mapping.get(standard_column)
        default_index = (
            options.index(default_source)
            if default_source in options
            else 0
        )
        required_label = "Required" if standard_column in REQUIRED_COLUMNS else "Optional"
        label_left, input_right = st.columns([1, 2])
        with label_left:
            st.markdown(f"**{standard_column}**")
            st.caption(required_label)
        with input_right:
            selected_source = st.selectbox(
                f"{standard_column} source column",
                options=options,
                index=default_index,
                key=f"map_{file_key}_{standard_column}",
                label_visibility="collapsed",
            )
        mapping[standard_column] = (
            None
            if selected_source == NO_COLUMN_OPTION
            else selected_source
        )

    return mapping


if __name__ == "__main__":
    main()
