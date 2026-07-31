from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import BinaryIO, Iterable, Mapping

import pandas as pd


STANDARD_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]

REQUIRED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
]

OPTIONAL_COLUMNS = ["Description", "Country"]

CSV_EXTENSIONS = {".csv"}
EXCEL_EXTENSIONS = {".xlsx"}
SUPPORTED_EXTENSIONS = CSV_EXTENSIONS | EXCEL_EXTENSIONS

CSV_ENCODINGS = ("utf-8-sig", "utf-8", "latin1")

NO_COLUMN_OPTION = "-- Not mapped --"

DEFAULT_COLUMN_ALIASES = {
    "InvoiceNo": ("InvoiceNo", "Invoice"),
    "StockCode": ("StockCode",),
    "Description": ("Description",),
    "Quantity": ("Quantity",),
    "InvoiceDate": ("InvoiceDate",),
    "UnitPrice": ("UnitPrice", "Price"),
    "CustomerID": ("CustomerID", "Customer ID"),
    "Country": ("Country",),
}


class UnsupportedFileTypeError(ValueError):
    pass


@dataclass(frozen=True)
class MappingValidationResult:
    missing_required: list[str]
    duplicate_sources: list[str]
    unknown_sources: list[str]

    @property
    def is_valid(self) -> bool:
        return not (
            self.missing_required
            or self.duplicate_sources
            or self.unknown_sources
        )

    def messages(self) -> list[str]:
        messages = []
        if self.missing_required:
            missing = ", ".join(self.missing_required)
            messages.append(f"Missing required mapping: {missing}")
        if self.duplicate_sources:
            duplicates = ", ".join(self.duplicate_sources)
            messages.append(f"One source column is mapped more than once: {duplicates}")
        if self.unknown_sources:
            unknown = ", ".join(self.unknown_sources)
            messages.append(f"Mapped source columns do not exist in the file: {unknown}")
        return messages


def get_file_extension(file_name: str) -> str:
    return Path(file_name).suffix.casefold()


def ensure_supported_file(file_name: str) -> None:
    extension = get_file_extension(file_name)
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension}'. Please upload one of: {supported}"
        )


def read_uploaded_columns(file: BinaryIO, file_name: str) -> list[str]:
    ensure_supported_file(file_name)
    extension = get_file_extension(file_name)

    if extension in CSV_EXTENSIONS:
        df_header = _read_csv(file, nrows=0)
        return normalize_columns(df_header.columns)

    xls = _open_excel(file)
    all_columns: list[str] = []
    for sheet_name in xls.sheet_names:
        df_header = xls.parse(sheet_name, nrows=0)
        all_columns.extend(normalize_columns(df_header.columns))
    return list(dict.fromkeys(all_columns))


def read_uploaded_dataframe(file: BinaryIO, file_name: str) -> pd.DataFrame:
    ensure_supported_file(file_name)
    extension = get_file_extension(file_name)

    if extension in CSV_EXTENSIONS:
        return normalize_dataframe_columns(_read_csv(file))

    xls = _open_excel(file)
    frames = [
        normalize_dataframe_columns(xls.parse(sheet_name))
        for sheet_name in xls.sheet_names
    ]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_default_mapping(source_columns: Iterable[str]) -> dict[str, str | None]:
    source_columns = list(source_columns)
    normalized_source = {
        normalize_column_name(column): column
        for column in source_columns
    }

    mapping: dict[str, str | None] = {}
    used_sources: set[str] = set()

    for standard_column in STANDARD_COLUMNS:
        aliases = DEFAULT_COLUMN_ALIASES[standard_column]
        matched_source = None
        for alias in aliases:
            source = normalized_source.get(normalize_column_name(alias))
            if source and source not in used_sources:
                matched_source = source
                break
        mapping[standard_column] = matched_source
        if matched_source:
            used_sources.add(matched_source)

    return mapping


def validate_mapping(
    standard_to_source: Mapping[str, str | None],
    source_columns: Iterable[str] | None = None,
) -> MappingValidationResult:
    selected_sources = [
        source
        for source in standard_to_source.values()
        if source and source != NO_COLUMN_OPTION
    ]
    source_counts = Counter(selected_sources)

    missing_required = [
        column
        for column in REQUIRED_COLUMNS
        if not standard_to_source.get(column)
        or standard_to_source.get(column) == NO_COLUMN_OPTION
    ]
    duplicate_sources = [
        source
        for source, count in source_counts.items()
        if count > 1
    ]

    known_sources = set(source_columns) if source_columns is not None else set()
    unknown_sources = []
    if known_sources:
        unknown_sources = [
            source
            for source in selected_sources
            if source not in known_sources
        ]

    return MappingValidationResult(
        missing_required=missing_required,
        duplicate_sources=duplicate_sources,
        unknown_sources=unknown_sources,
    )


def mapping_to_rename_dict(
    standard_to_source: Mapping[str, str | None],
) -> dict[str, str]:
    return {
        source: standard_column
        for standard_column, source in standard_to_source.items()
        if source and source != NO_COLUMN_OPTION
    }


def apply_column_mapping(
    df: pd.DataFrame,
    standard_to_source: Mapping[str, str | None],
) -> pd.DataFrame:
    validation = validate_mapping(standard_to_source, df.columns)
    if not validation.is_valid:
        raise ValueError("; ".join(validation.messages()))

    rename_dict = mapping_to_rename_dict(standard_to_source)
    return df.rename(columns=rename_dict)


def normalize_columns(columns: Iterable[object]) -> list[str]:
    return [str(column).strip() for column in columns]


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = normalize_columns(df.columns)
    return df


def normalize_column_name(column: object) -> str:
    compact = re.sub(r"[\s_\-]+", "", str(column))
    return compact.casefold()


def _read_csv(file: BinaryIO, nrows: int | None = None) -> pd.DataFrame:
    last_error: UnicodeDecodeError | None = None
    for encoding in CSV_ENCODINGS:
        _seek_start(file)
        try:
            return pd.read_csv(file, nrows=nrows, encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error

    if last_error:
        raise last_error
    raise ValueError("Unable to read CSV file.")


def _open_excel(file: BinaryIO) -> pd.ExcelFile:
    _seek_start(file)
    return pd.ExcelFile(file)


def _seek_start(file: BinaryIO) -> None:
    if hasattr(file, "seek"):
        file.seek(0)
