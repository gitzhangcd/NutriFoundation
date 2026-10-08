from __future__ import annotations

import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
import calendar
from typing import Protocol
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class PubMedArticle:
    pmid: str
    title: str
    journal: str | None
    publication_date: date | None
    authors: tuple[str, ...]
    doi: str | None
    pmcid: str | None
    publication_types: tuple[str, ...]
    abstract: str | None = None
    publication_date_raw: str | None = None
    publication_date_precision: str = "unknown"
    publication_date_start: date | None = None
    publication_date_end: date | None = None


class PubMedProvider(Protocol):
    def fetch_articles(self, pmids: list[str]) -> list[PubMedArticle]: ...


_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def _text(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    value = "".join(node.itertext()).strip()
    return value or None


def _date_details(article: ET.Element) -> tuple[date | None, str | None, str, date | None, date | None]:
    pd = article.find(".//JournalIssue/PubDate")
    if pd is None:
        return None, None, "unknown", None, None

    year = _text(pd.find("Year"))
    month = _text(pd.find("Month"))
    day = _text(pd.find("Day"))

    raw = ET.tostring(pd, encoding="unicode")

    if not year or not year.isdigit():
        # Seasonal/ranged MedlineDate is preserved, never coerced to January 1.
        return None, raw, "unresolved", None, None
    try:
        y = int(year)
        if not month:
            if day:
                return None, raw, "unresolved", None, None
            return None, raw, "year", date(y, 1, 1), date(y, 12, 31)
        m = int(month) if month.isdigit() else _MONTHS[month[:3].title()]
        if not day:
            return None, raw, "month", date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])
        exact = date(y, m, int(day))
        return exact, raw, "day", exact, exact
    except (ValueError, KeyError):
        return None, raw, "unresolved", None, None


def _pub_date(article: ET.Element) -> date | None:
    return _date_details(article)[0]


def parse_pubmed_xml(xml_text: str) -> list[PubMedArticle]:
    root = ET.fromstring(xml_text)
    out: list[PubMedArticle] = []

    for item in root.findall(".//PubmedArticle"):
        pmid = _text(item.find(".//MedlineCitation/PMID"))
        title = _text(item.find(".//Article/ArticleTitle"))
        if not pmid or not title:
            continue

        journal = _text(item.find(".//Article/Journal/Title"))

        authors = []
        for author in item.findall(".//Article/AuthorList/Author"):
            collective = _text(author.find("CollectiveName"))
            if collective:
                authors.append(collective)
                continue
            given = _text(author.find("ForeName")) or _text(author.find("Initials")) or ""
            last = _text(author.find("LastName")) or ""
            name = " ".join(x for x in (given, last) if x).strip()
            if name:
                authors.append(name)

        identifiers = {
            node.attrib.get("IdType"): _text(node)
            for node in item.findall(".//PubmedData/ArticleIdList/ArticleId")
        }

        publication_types = tuple(
            value
            for value in (
                _text(node)
                for node in item.findall(".//Article/PublicationTypeList/PublicationType")
            )
            if value
        )

        abstract_parts = [
            value for value in
            (_text(node) for node in item.findall(".//Article/Abstract/AbstractText"))
            if value
        ]

        exact_date, date_raw, precision, start, end = _date_details(item)
        out.append(
            PubMedArticle(
                pmid=pmid,
                title=title,
                journal=journal,
                publication_date=exact_date,
                authors=tuple(authors),
                doi=identifiers.get("doi"),
                pmcid=identifiers.get("pmc"),
                publication_types=publication_types,
                abstract="\n".join(abstract_parts) if abstract_parts else None,
                publication_date_raw=date_raw,
                publication_date_precision=precision,
                publication_date_start=start,
                publication_date_end=end,
            )
        )

    return out


class NCBIClient:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        *,
        email: str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
    ):
        self.email = email or os.getenv("NUTRIFOUNDATION_EMAIL")
        self.api_key = api_key or os.getenv("NCBI_API_KEY")
        self.timeout = timeout

    def _get(self, endpoint: str, params: dict[str, str]) -> str:
        params = dict(params)
        params.setdefault("tool", "NutriFoundationEngine")
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.base_url}/{endpoint}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "NutriFoundationEngine/0.2"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8")


class PubMedConnector(NCBIClient):
    def fetch_articles(self, pmids: list[str]) -> list[PubMedArticle]:
        if not pmids:
            return []
        xml = self._get(
            "efetch.fcgi",
            {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"},
        )
        return parse_pubmed_xml(xml)


class PMCConnector(NCBIClient):
    def fetch_full_text_xml(self, pmcid: str) -> str:
        normalized = pmcid.upper().removeprefix("PMC")
        return self._get(
            "efetch.fcgi",
            {"db": "pmc", "id": normalized, "retmode": "xml"},
        )
