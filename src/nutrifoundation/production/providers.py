from __future__ import annotations

import time
import urllib.parse
import urllib.request
from uuid import uuid4

from nutrifoundation.connectors.ncbi import NCBIClient
from .acquisition import SnapshotService
from .jobs import JobQueue


class RateDeferred(Exception):
    def __init__(self,seconds: float):
        self.seconds=seconds
        super().__init__("Provider request deferred by shared rate budget")


class NCBIRawAdapter(NCBIClient):
    """Official EFetch raw XML with shared SQLite rate budget and byte preservation.

    Not an OA-license certification service. Callers must bind acquired scope
    and supplied license, and retain API/rights qualification separately.
    """
    def __init__(self,snapshots: SnapshotService,queue: JobQueue,**kwargs):
        super().__init__(**kwargs)
        self.snapshots=snapshots
        self.queue=queue

    def fetch(self,identifier: str, *, database: str, source_id: str,
              source_version: str, license: str):
        if database not in {"pubmed","pmc"}:
            raise ValueError("Unsupported NCBI intake")
        clean=identifier.upper().removeprefix("PMC")
        if not clean.isdigit():
            raise ValueError("One numeric PMID/PMCID required")
        from .models import digest
        key_scope=digest(self.api_key) if self.api_key else "anonymous"
        delay=self.queue.reserve_request("NCBI-EUtilities:"+key_scope,
            requests_per_second=10 if self.api_key else 3)
        if delay > 30:
            raise RateDeferred(delay)
        if delay > 0:
            time.sleep(delay)
        params={"db":database,"id":clean,"retmode":"xml","tool":"NutriFoundationEngine"}
        if self.email:
            params["email"]=self.email
        if self.api_key:
            params["api_key"]=self.api_key
        url=self.base_url+"/efetch.fcgi?"+urllib.parse.urlencode(params)
        request=urllib.request.Request(url,headers={"User-Agent":"NutriFoundationEngine/D0"})
        try:
            with urllib.request.urlopen(request,timeout=self.timeout) as response:
                data=response.read(32*1024*1024+1)
                status=response.status
                content_type=response.headers.get("Content-Type","")
        except Exception as error:
            # Exception URL strings can contain API credentials; persist only class.
            self.snapshots.store.event("acquisition_failed",source_id,{"provider":"NCBI","database":database,"identifier":clean,"error_class":type(error).__name__})
            raise ValueError("NCBI acquisition failed; see sanitized event") from None
        if status!=200 or len(data)>32*1024*1024:
            raise ValueError("NCBI response failed status/size qualification")
        from xml.etree import ElementTree as ET
        root=ET.fromstring(data)
        if root.find(".//ERROR") is not None:
            raise ValueError("NCBI returned an XML error, not requested content")
        if database=="pubmed":
            ids=[n.text for n in root.findall(".//MedlineCitation/PMID")]
        else:
            ids=[n.text.removeprefix("PMC") for n in root.findall(".//article-id[@pub-id-type='pmc']") if n.text]
        if clean not in ids:
            raise ValueError("Requested identity absent from NCBI payload")
        snapshot=self.snapshots.ingest(data,source_id=source_id,source_version=source_version,
            format="JATS_XML",content_scope="fulltext" if database=="pmc" else "metadata",
            license=license,origin=f"NCBI:{database}:{clean}")
        self.snapshots.store.event("http_acquisition",snapshot.snapshot_id,{"event_id":uuid4().hex,
            "provider":"NCBI","database":database,"identifier":clean,"status":status,
            "content_type":content_type,"scope":snapshot.content_scope,"sha256":snapshot.content_sha256})
        return snapshot
