from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .ncbi import PubMedArticle


class FixturePubMedConnector:
    def __init__(self, path: str | Path):
        records = json.loads(Path(path).read_text(encoding="utf-8"))
        self._records = {str(record["pmid"]): record for record in records}

    def fetch_articles(self, pmids: list[str]) -> list[PubMedArticle]:
        out = []
        for pmid in pmids:
            record = self._records[str(pmid)]
            publication_date = (
                date.fromisoformat(record["publication_date"])
                if record.get("publication_date")
                else None
            )
            out.append(
                PubMedArticle(
                    pmid=str(record["pmid"]),
                    title=record["title"],
                    journal=record.get("journal"),
                    publication_date=publication_date,
                    authors=tuple(record.get("authors", [])),
                    doi=record.get("doi"),
                    pmcid=record.get("pmcid"),
                    publication_types=tuple(record.get("publication_types", [])),
                    abstract=record.get("abstract"),
                )
            )
        return out
