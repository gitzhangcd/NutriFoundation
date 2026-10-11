"""WB-P1.1-B1 immutable *synthetic reference* Source Packages.

Deliberately does NOT import files, PDFs, translations, OCR, MinerU outputs,
new EA sources, patient records, original units or true scientific evidence.
The only authoritative text remains inside the original EvidenceEngine.
"""
from __future__ import annotations

import json
import re
from ea_runtime import digest, encoded, when
from tpa_runtime import block, utcnow

PACKAGE_PATTERN = re.compile(r"SPKG-SYN-[A-Z0-9-]{3,40}\Z")
KEY_PATTERN = re.compile(r"[A-Za-z0-9_.:-]{8,100}\Z")
CONTRACT = "WB-SOURCE-PACKAGE-v0.1"
SYNTHETIC_KIND = "EXISTING_SYNTHETIC_SOURCE"
ADAPTER = "SYNTHETIC_FIXTURE_ADAPTER"
STATUS = "SYNTHETIC_REFERENCE_ONLY"


class SourcePackages:
    def __init__(self, tpa):
        self.tpa = tpa
        with self.tpa.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tpa_source_packages (
                    package_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    record TEXT NOT NULL,
                    UNIQUE(source_id,revision_id)
                );
                CREATE TABLE IF NOT EXISTS tpa_source_package_replays (
                    request_key TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    package_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    receipt TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS tpa_package_no_update
                    BEFORE UPDATE ON tpa_source_packages
                    BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SOURCE_PACKAGE'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_package_no_delete
                    BEFORE DELETE ON tpa_source_packages
                    BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SOURCE_PACKAGE'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_package_replay_no_update
                    BEFORE UPDATE ON tpa_source_package_replays
                    BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SOURCE_PACKAGE_REPLAY'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_package_replay_no_delete
                    BEFORE DELETE ON tpa_source_package_replays
                    BEGIN SELECT RAISE(ABORT,'IMMUTABLE_SOURCE_PACKAGE_REPLAY'); END;
            """)

    def _validate(self, role, manifest):
        self.tpa.role(role, ("producer",))
        if manifest["schema_version"] != CONTRACT:
            block("UNSUPPORTED_PACKAGE_CONTRACT")
        if manifest["import_kind"] != SYNTHETIC_KIND or manifest["parser_adapter"] != ADAPTER:
            block("SYNTHETIC_ONLY_REAL_SOURCE_DENY")
        if manifest["rights_status"] != "SYNTHETIC_FIXTURE":
            block("SOURCE_RIGHTS_NOT_QUALIFIED")
        source = self.tpa.registered_source(manifest["source_id"], manifest["revision_id"])
        if manifest["canonical_document_sha256"] != source["canonical_document_sha256"]:
            block("SOURCE_REVISION_MISMATCH")
        if manifest["source_type"] != source["source_type"]:
            block("SOURCE_TYPE_MISMATCH")
        if manifest["profile_id"] != source["source_type_profile_id"]:
            block("PROFILE_SOURCE_TYPE_MISMATCH")
        if source["rights_status"] != "SYNTHETIC_FIXTURE":
            block("SOURCE_RIGHTS_NOT_QUALIFIED")
        units = source["units"]
        # Structured coordinates refer to the immutable source; no original text leaves EA.
        structure = [{
            "unit_id":unit["unit_id"],
            "ordinal":i,
            "element_kind":"PARAGRAPH",
            "utf16_length":len(unit["text"].encode("utf-16-le"))//2,
            "unit_text_sha256":digest(unit["text"].encode("utf-8"))
        } for i,unit in enumerate(units)]
        if not structure or any(not x["unit_id"] or x["utf16_length"]<1 for x in structure):
            block("INVALID_STRUCTURED_SOURCE")
        parent = manifest.get("parent_package_id")
        if parent is not None:
            # No r2 fixture is seeded currently. Never fabricate a revision chain.
            if not isinstance(parent,str) or not PACKAGE_PATTERN.fullmatch(parent):
                block("INVALID_SOURCE_LINEAGE")
            with self.tpa.connect() as db:
                row = db.execute("SELECT record FROM tpa_source_packages WHERE package_id=?",
                                 (parent,)).fetchone()
            if not row:
                block("PARENT_PACKAGE_NOT_FOUND")
            prior = json.loads(row["record"])
            if prior["source_id"] != source["source_id"] or prior["revision_id"] == source["revision_id"]:
                block("INVALID_SOURCE_LINEAGE")
            # A parent must be older in authoritative source time, not merely by ID.
            earlier = self.tpa.registered_source(prior["source_id"],prior["revision_id"])
            if when(earlier["available_at"]) >= when(source["available_at"]):
                block("INVALID_SOURCE_LINEAGE")
        normalized = {k:manifest[k] for k in ("schema_version","import_kind","parser_adapter",
                                             "source_id","revision_id","source_type","profile_id",
                                             "canonical_document_sha256","rights_status")}
        normalized["parent_package_id"] = parent
        signature = digest({"manifest":normalized,"structured_units":structure})
        return {
            "status":"VALIDATED_SYNTHETIC_REFERENCE",
            "contract":CONTRACT, "normalized_manifest":normalized,
            "structure_index":structure,
            "structure_sha256":digest(structure),
            "manifest_sha256":signature,
            "source_lineage":{"upstream":"EA_SEEDED_FIXTURE",
                              "source_id":source["source_id"],
                              "revision_id":source["revision_id"],
                              "parent_package_id":parent},
            "content_imported":False,"original_units_exposed":False,
            "scientific_capture":False,"gold_qualification":"NOT_ELIGIBLE",
            "real_source_qualified":False
        }

    def validate(self, role, manifest):
        return self._validate(role,manifest)

    def register(self, role, actor, body):
        self.tpa.role(role, ("producer",))
        package_id = body["package_id"]
        key = body["idempotency_key"]
        if not PACKAGE_PATTERN.fullmatch(package_id):
            block("INVALID_PACKAGE_ID")
        if not KEY_PATTERN.fullmatch(key):
            block("INVALID_IDEMPOTENCY_KEY")
        manifest = {k:v for k,v in body.items() if k not in ("package_id","idempotency_key")}
        # Important: re-validate authoritative EA source before applying replay.
        validated = self._validate(role,manifest)
        req_hash=digest({"package_id":package_id,"manifest":validated["normalized_manifest"]})
        with self.tpa.lock,self.tpa.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT * FROM tpa_source_package_replays WHERE request_key=?",
                           (key,)).fetchone()
            if old:
                if old["actor"]!=actor or old["request_digest"]!=req_hash or old["package_id"]!=package_id:
                    block("IDEMPOTENCY_CONFLICT")
                return json.loads(old["receipt"])
            conflict=db.execute(
                "SELECT package_id FROM tpa_source_packages WHERE package_id=? OR (source_id=? AND revision_id=?)",
                (package_id,manifest["source_id"],manifest["revision_id"])).fetchone()
            if conflict:
                block("SOURCE_PACKAGE_ALREADY_REGISTERED")
            record={
                "package_id":package_id,
                "registered_by":actor,
                "registered_at":utcnow(),
                **validated["normalized_manifest"],
                "structure_index":validated["structure_index"],
                "structure_sha256":validated["structure_sha256"],
                "manifest_sha256":validated["manifest_sha256"],
                "lineage":validated["source_lineage"],
                "status":STATUS,
                "scientific_capture":False,
                "gold_qualification":"NOT_ELIGIBLE"
            }
            receipt={"package":record,"idempotent_replay":False,
                     "original_units_exposed":False,
                     "content_imported":False,"real_source_import_enabled":False}
            db.execute("INSERT INTO tpa_source_packages(package_id,source_id,revision_id,record) VALUES(?,?,?,?)",
                       (package_id,record["source_id"],record["revision_id"],encoded(record).decode()))
            db.execute("INSERT INTO tpa_source_package_replays(request_key,request_digest,package_id,actor,receipt) VALUES(?,?,?,?,?)",
                       (key,req_hash,package_id,actor,encoded(receipt).decode()))
            self.tpa.event(db,package_id,actor,"SYNTHETIC_SOURCE_PACKAGE_REGISTERED",{
                "package_id":package_id,"source_id":record["source_id"],
                "revision_id":record["revision_id"],"manifest_sha256":record["manifest_sha256"],
                "structure_sha256":record["structure_sha256"],"scientific_capture":False
            })
            return receipt

    def _load(self, role, record):
        self.tpa.role(role, ("manager","producer"))
        value=json.loads(record["record"])
        source=self.tpa.registered_source(value["source_id"],value["revision_id"])
        if source["canonical_document_sha256"]!=value["canonical_document_sha256"]:
            block("SOURCE_REVISION_MISMATCH")
        if (source["source_type"]!=value["source_type"] or
            source["source_type_profile_id"]!=value["profile_id"] or
            source["rights_status"]!=value["rights_status"]):
            block("SOURCE_REFERENCE_DRIFT")
        normalized={k:value[k] for k in ("schema_version","import_kind","parser_adapter",
                                        "source_id","revision_id","source_type","profile_id",
                                        "canonical_document_sha256","rights_status","parent_package_id")}
        if (digest(value["structure_index"])!=value["structure_sha256"] or
            digest({"manifest":normalized,"structured_units":value["structure_index"]})!=value["manifest_sha256"]):
            block("SOURCE_PACKAGE_MANIFEST_DRIFT")
        check=digest([{
            "unit_id":u["unit_id"],"ordinal":i,"element_kind":"PARAGRAPH",
            "utf16_length":len(u["text"].encode("utf-16-le"))//2,
            "unit_text_sha256":digest(u["text"].encode("utf-8"))
        } for i,u in enumerate(source["units"])])
        if check!=value["structure_sha256"]:
            block("SOURCE_STRUCTURE_DRIFT")
        return value

    def listing(self, role, limit=25, offset=0):
        self.tpa.role(role, ("manager","producer"))
        if type(limit) is not int or type(offset) is not int or not (1<=limit<=100) or not(0<=offset<=100000):
            block("INVALID_PAGINATION")
        with self.tpa.connect() as db:
            total=db.execute("SELECT COUNT(*) FROM tpa_source_packages").fetchone()[0]
            rows=db.execute("SELECT record FROM tpa_source_packages ORDER BY package_id LIMIT ? OFFSET ?",
                            (limit,offset)).fetchall()
        return {"packages":[self._load(role,r) for r in rows],
                "total":total,"limit":limit,"offset":offset,
                "synthetic_only":True,"original_units_exposed":False,
                "real_import_enabled":False}

    def detail(self, role, package_id):
        self.tpa.role(role, ("manager","producer"))
        if not PACKAGE_PATTERN.fullmatch(package_id):
            block("INVALID_PACKAGE_ID")
        with self.tpa.connect() as db:
            row=db.execute("SELECT record FROM tpa_source_packages WHERE package_id=?",
                           (package_id,)).fetchone()
        if row is None: block("SOURCE_PACKAGE_NOT_FOUND")
        return {"package":self._load(role,row),"original_units_exposed":False,
                "content_imported":False,"real_source_qualified":False}
