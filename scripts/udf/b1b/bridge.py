"""Versioned, narrow D0 bridge for shared source identities only.

Do not migrate legacy scientific records or project data to a model. D0 uses bare
object_id references; a bridge-local ID maps one-to-one to a particular immutable
B1 revision. The sidecar retains version semantics absent from the legacy envelope.
"""
from contract import canon,digest,ref,require,ContractError,validate_set,resolve,validate_slot
from copy import deepcopy
from pathlib import Path
import json,sys,hashlib

BRIDGE_VERSION="UDF-B1-D0-SHARED-BRIDGE-0.1"
PIN="09e854dced620645c49b72f5c4040610f162ef59"
KINDS={"SourceArtifact","SourceAnchor"}
LEGACY_FIELDS={"object_id","revision_id","kind","schema_version","lifecycle","producer_role","created_time","provenance_refs","dependency_refs","source_class","purpose_release_ref","supersedes_ref","instance_class"}
ART_FIELDS={"artifact_type","external_ids","qualification_status","title","namespace","file_sha256","bytes","source_role","version_status"}
ANCH_FIELDS={"source_ref","source_version","locator","content_or_content_ref","integrity"}
SIDECAR_FIELDS={"bridge_id","b1_ref","b1_schema_version","b1_contract_version","b1_clock_axis","b1_purpose","b1_purpose_release_ref","b1_supersedes_ref"}
def bridge_id(r):return "UDFA:"+digest([BRIDGE_VERSION,r])[:40]
def legacy_revision(obj):
    x=dict(obj);x.pop("revision_id",None);return digest(x)
def check_legacy_envelope(o):
    require(o["kind"] in KINDS,"D0_BRIDGE_KIND_UNAUTHORIZED")
    require(set(o)==LEGACY_FIELDS|(ART_FIELDS if o["kind"]=="SourceArtifact" else ANCH_FIELDS),"D0_BRIDGE_FIELDS")
    require(o["schema_version"]=="NDF-D0-v0.1" and o["lifecycle"]=="DRAFT" and o["purpose_release_ref"]=="CURATION_DEV" and o["supersedes_ref"] is None,"D0_BRIDGE_PURPOSE_OR_LIFECYCLE")
    require(o["source_class"]=="REAL_DATA" and o["instance_class"]=="REAL_SOURCE_GROUNDED","D0_BRIDGE_SOURCE_INSTANCE")
    require(o["revision_id"]==legacy_revision(o),"D0_BRIDGE_REVISION")
def forward(objects):
    validate_set(objects)
    selected=[o for o in objects if o["kind"] in KINDS]
    ids={ref(o):bridge_id(ref(o)) for o in selected}
    require(len(set(ids.values()))==len(ids),"D0_BRIDGE_ID_COLLISION")
    legacy=[];side=[]
    for o in selected:
        p=o["payload"];bid=ids[ref(o)]
        require(all(r in ids for r in o["provenance_refs"]+o["dependency_refs"]),"D0_BRIDGE_DEPENDENCY_SCOPE")
        require(o["purpose_release_ref"]["tag"]=="PENDING" and o["supersedes_ref"]["tag"]=="NOT_APPLICABLE","D0_BRIDGE_SOURCE_RELEASE_OR_SUPERSESSION")
        z={"object_id":bid,"kind":o["kind"],"schema_version":"NDF-D0-v0.1","lifecycle":"DRAFT",
           "producer_role":o["producer_role"],"created_time":o["created_time"],"provenance_refs":[ids[r] for r in o["provenance_refs"]],
           "dependency_refs":[ids[r] for r in o["dependency_refs"]],"source_class":o["source_class"],"purpose_release_ref":"CURATION_DEV",
           "supersedes_ref":None,"instance_class":o["instance_class"]}
        if o["kind"]=="SourceArtifact":
            z.update({"artifact_type":"DATASET_FILE","external_ids":[],"qualification_status":"DRAFT_NOT_REFERENCE_QUALIFIED",
                      "title":"Source-scoped dataset artifact",**deepcopy(p)})
        else:
            require(p["source_ref"] in ids and p["content"]["tag"]=="UNAVAILABLE" and p["content"]["reason"]=="WITHHELD","D0_BRIDGE_CONTENT_OR_SOURCE")
            z.update({"source_ref":ids[p["source_ref"]],"source_version":p["integrity"],"locator":deepcopy(p["locator"]),
                      "content_or_content_ref":deepcopy(p["content"]),"integrity":p["integrity"]})
        z["revision_id"]=legacy_revision(z)
        check_legacy_envelope(z);legacy.append(z)
        side.append({"bridge_id":bid,"b1_ref":ref(o),"b1_schema_version":o["schema_version"],"b1_contract_version":o["contract_version"],
                     "b1_clock_axis":o["clock_axis"],"b1_purpose":o["purpose"],
                     "b1_purpose_release_ref":deepcopy(o["purpose_release_ref"]),"b1_supersedes_ref":deepcopy(o["supersedes_ref"])})
    return legacy,side
def reverse(legacy,side):
    ix={x["object_id"]:x for x in legacy};sx={x["bridge_id"]:x for x in side}
    require(len(ix)==len(legacy)==len(sx)==len(side) and set(ix)==set(sx),"D0_BRIDGE_ONE_TO_ONE")
    require(len({s["b1_ref"] for s in side})==len(side),"D0_BRIDGE_DUPLICATE_REVISION")
    # Validate every transport envelope before traversing references, so a wrong
    # object kind cannot be hidden by reference traversal order.
    for z in legacy:check_legacy_envelope(z)
    out=[]
    for bid,z in ix.items():
        check_legacy_envelope(z);s=sx[bid]
        require(set(s)==SIDECAR_FIELDS and bid==bridge_id(s["b1_ref"]),"D0_BRIDGE_SIDECAR")
        require(s["b1_purpose"]=="CURATION_DEV" and s["b1_clock_axis"]=="AUDIT_UTC","D0_BRIDGE_CLOCK_OR_PURPOSE")
        validate_slot(s["b1_purpose_release_ref"]);validate_slot(s["b1_supersedes_ref"])
        require(s["b1_purpose_release_ref"]["tag"]=="PENDING" and s["b1_supersedes_ref"]["tag"]=="NOT_APPLICABLE","D0_BRIDGE_SOURCE_RELEASE_OR_SUPERSESSION")
        require(all(r in ix for r in z["provenance_refs"]+z["dependency_refs"]),"D0_BRIDGE_ORPHAN")
        if z["kind"]=="SourceArtifact":
            require(z["artifact_type"]=="DATASET_FILE" and z["external_ids"]==[] and z["qualification_status"]=="DRAFT_NOT_REFERENCE_QUALIFIED" and z["title"]=="Source-scoped dataset artifact","D0_BRIDGE_ARTIFACT_PROMOTION")
            p={k:deepcopy(z[k]) for k in ("namespace","file_sha256","bytes","source_role","version_status")}
        else:
            require(z["source_ref"] in ix and ix[z["source_ref"]]["kind"]=="SourceArtifact","D0_BRIDGE_TYPED_SOURCE")
            require(z["source_version"]==z["integrity"]==ix[z["source_ref"]]["file_sha256"],"D0_BRIDGE_SOURCE_HASH")
            c=z["content_or_content_ref"];validate_slot(c)
            require(c["tag"]=="UNAVAILABLE" and c["reason"]=="WITHHELD","D0_BRIDGE_CONTENT_OR_SOURCE")
            p={"source_ref":sx[z["source_ref"]]["b1_ref"],"locator":deepcopy(z["locator"]),"integrity":z["integrity"],"content":deepcopy(c),"source_class":z["source_class"]}
        oid,rv=s["b1_ref"].rsplit("@",1)
        obj={"object_id":oid,"revision_id":rv,"kind":z["kind"],"schema_version":s["b1_schema_version"],
             "contract_version":s["b1_contract_version"],"lifecycle":z["lifecycle"],"producer_role":z["producer_role"],
             "created_time":z["created_time"],"clock_axis":s["b1_clock_axis"],
             "provenance_refs":[sx[x]["b1_ref"] for x in z["provenance_refs"]],"dependency_refs":[sx[x]["b1_ref"] for x in z["dependency_refs"]],
             "source_class":z["source_class"],"instance_class":z["instance_class"],"purpose_release_ref":deepcopy(s["b1_purpose_release_ref"]),
             "purpose":s["b1_purpose"],"supersedes_ref":deepcopy(s["b1_supersedes_ref"]),"payload":p}
        out.append(obj)
    validate_set(out)
    return out
def migration_status(obj):
    if "instance_class" not in obj:return "HOLD_LEGACY_INSTANCE_CLASS_UNRESOLVED"
    return "HOLD_EXPLICIT_KIND_SPECIFIC_MIGRATION_REQUIRED"
def verify_snapshot(root):
    m=json.loads((root/"manifest.json").read_text());require(m["commit"]==PIN and len(m["files"])==12,"D0_SNAPSHOT_PIN")
    for f in m["files"]:
        p=root/f["path"];b=p.read_bytes()
        g=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        require(g==f["git_blob"] and hashlib.sha256(b).hexdigest()==f["sha256"],"D0_SNAPSHOT_HASH")
    return m
def run_d0(root,legacy):
    # Load the exact verified prior runtime, not the new guard implementation.
    m=verify_snapshot(root);sys.path.insert(0,str(root/"src"))
    from nutrifoundation.ndf.d0 import ValidationContext,validate_objects
    def call(o,ctx,id):
        r=validate_objects(o,ValidationContext(**ctx),run_id=id)
        return r.qualification,sorted({x.error_code for x in r.checks if x.error_code})
    q,codes=call(legacy,{"authorized_view":"CURATION_DEV"},"B1B-shared-bridge")
    require(q=="PASS" and not codes,"D0_RUNTIME_REJECTS_BRIDGE")
    tests=[]
    base=root/"fixtures/ndf/d0"
    fixtures=json.loads((base/"runtime_qualification/a2_8_plus_2.json").read_text())
    for t in ("negative","positive"):
        for x in fixtures[t]:
            q,c=call(x["objects"],x["context"],x["fixture_id"])
            exp=sorted(x.get("expected_error_codes",[]))
            passed=(q==("FAIL" if t=="negative" else "PASS") and c==exp)
            tests.append({"test":x["fixture_id"],"expected":"FAIL" if t=="negative" else "PASS","observed":q,"expected_codes":exp,"observed_codes":c,"pass":passed})
    for f in sorted((base/"real_objects").glob("*.json")):
        x=json.loads(f.read_text());q,c=call(x["objects"],x["context"],x["case_id"])
        tests.append({"test":"historical_real_"+("D1" if len(x["objects"])==3 else "D2"),"expected":"PASS","observed":q,"observed_codes":c,"pass":q=="PASS" and not c,
                      "legacy_missing_instance_class":sum(migration_status(o)=="HOLD_LEGACY_INSTANCE_CLASS_UNRESOLVED" for o in x["objects"]),
                      "legacy_object_count":len(x["objects"]),"migration":"NOT_EXECUTED"})
    require(len(tests)==12 and all(x["pass"] for x in tests),"D0_LEGACY_REGRESSION")
    return {"bridge_runtime_status":"PASS","pinned_commit":m["commit"],"verified_snapshot_files":len(m["files"]),
            "historical_tests":tests,"historical_test_count":len(tests),"historical_test_passed":sum(x["pass"] for x in tests)}
