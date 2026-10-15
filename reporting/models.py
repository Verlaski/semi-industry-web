from dataclasses import dataclass, field
from typing import List


@dataclass
class TableModel:
    headers: List[str]
    rows: List[List[str]]
    widths: List[float]


@dataclass
class SectionModel:
    title: str
    paragraphs: List[str] = field(default_factory=list)
    tables: List[TableModel] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)
    new_page: bool = False


@dataclass
class ReportModel:
    report_type: str
    title: str
    data_version: str
    generated_at: str
    summary: List[str]
    sections: List[SectionModel]
    sources: list
    disclaimer: str
    quotes: list = field(default_factory=list)
