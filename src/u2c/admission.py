"""Mandatory U2-C consumer boundary for the validated development projection.

This is not a research release or a replacement for an OS-level access-control system.
Consumers must use this entry rather than treating a legacy JSONL as qualified input.
"""
import argparse,collections as C,copy
from core import *
from runtime import verify,common,new_gov
from baseline import local,file_check

class Admission:
    def __init__(self,rt):
        self.rt=rt;self.b=rt.b
    def projection(self,o):
        """Validate supplied projected record, including exact recomputation from
        immutable approved sources. Reject even if a forged object is re-sealed."""
        self.b.schemas.validate(o)
        old=o["governance"]["legacy_ref"]
        if old is None:
            expected=lookup(self.rt.new,ref(o))
        else:
            x=lookup(self.b.idx,old)
            expected=self.rt.project(x,validate=True)
        require(canon(expected)==canon(o),"CURRENT_PROJECTION_NOT_AUTHORIZED")
        return expected
    def view(self,legacy_ref):
        o=lookup(self.b.idx,legacy_ref)
        return self.projection(self.rt.project(o))
    def request(self,operation,refs):
        require(operation in self.b.policy["operation_policy"],"OPERATION_UNREGISTERED")
        try:
            if operation in ("inspect","candidate_inspect"):
                for r in refs:self.view(r)
            elif operation=="measurement_calculate":
                require(len(refs)==1,"MEASUREMENT_REQUEST_GRAIN")
                x=self.rt._gate_views.get(refs[0])
                # Quality HOLD has priority over definition and unit qualification.
                d=self.rt.decision(operation,refs)
                if x is None or d["reason"]=="QUALITY_RECORD_MISSING_OR_UNBOUND":return d
                self.projection(x)
                if "quality_ref" in x["governance"]:
                    q=self.rt.quality.get(x["governance"]["quality_ref"])
                    if q is None:return {"decision":"HOLD","reason":"QUALITY_RECORD_MISSING_OR_UNBOUND"}
                    self.projection(q)
                return d
            elif operation=="independent_evidence_count":
                for r in refs:
                    x=self.rt._family_views.get(r)
                    if x is None:return {"decision":"HOLD","reason":"SOURCE_FAMILY_MISSING"}
                    self.projection(x)
            return self.rt.decision(operation,refs)
        except (ContractError,KeyError,TypeError,ValueError) as e:
            # No unvalidated object or raw value is returned to the consumer.
            return {"decision":"HOLD","reason":str(e) if isinstance(e,ContractError) else "INVALID_REQUEST_OR_RECORD"}
    def compare_representation(self,left,right):
        """Compare actual declared representation preconditions, not scientific
        equivalence. Source-level unknown and distinct analytes block the comparison."""
        try:
            a=self.view(left);b=self.view(right)
            require(a["kind"]==b["kind"]=="MeasurementInterpretation","REF_KIND_MISMATCH")
            x=a["payload"];y=b["payload"]
            p=self.b.idx[x["source_measurement_ref"]]["payload"];q=self.b.idx[y["source_measurement_ref"]]["payload"]
            d=self.view(x["measurement_definition_ref"]);e=self.view(y["measurement_definition_ref"])
            cc=d["payload"]["component_ref"];dd=e["payload"]["component_ref"]
            require(cc==dd and "UNSPECIFIED" not in cc,"COMPONENT_DEFINITION_UNQUALIFIED")
            for z in (a,b):
                require(z["governance"].get("quality_status")!="HOLD_SOURCE_TOTAL_CONFLICT","HOLD_SOURCE_TOTAL_CONFLICT")
                require(z["governance"].get("semantic_overlay",{}).get("record_definition_status")!="PENDING_ORIGINAL_LABEL_AND_TRANSFORMATION","OFF_RECORD_COMPONENT_DEFINITION_UNRESOLVED")
            def tag(z):return z.get("value") if z.get("tag")=="VALUE" else None
            u=tag(x["interpretation_unit"]);v=tag(y["interpretation_unit"])
            exact_component_guard(unit_kind(u),unit_kind(v))
            compatible_basis(tag(x["interpretation_basis"]),tag(y["interpretation_basis"]),tag(p["preparation"]),tag(q["preparation"]))
            # No cross-source measurement equivalence or scientific calculation is qualified.
            return {"decision":"HOLD","reason":"SCIENTIFIC_MEASUREMENT_COMPARABILITY_NOT_QUALIFIED"}
        except ContractError as ex:return {"decision":"HOLD","reason":str(ex)}

def supplement_off(rt,acquisition_path,expected_sha):
    """Read a new bounded API manifest and verify its exact bytes, products and
    original fields. This does not modify any prior snapshot or interpretation."""
    b=rt.b;path=file_check(b.root,acquisition_path,expected_sha);a=load(path)
    new={};stats=C.Counter();basis=C.Counter();field=C.Counter();domain=["OFF_ODBL_REVIEW"]
    for x in a["attempts"]:
        if not x.get("file"):continue
        p=path.parent/x["file"];require(p.is_relative_to(b.root),"OFF_SOURCE_PATH")
        f=file_check(b.root,p.relative_to(b.root),x["sha256"]);require(f.stat().st_size==x["bytes"],"OFF_SOURCE_SIZE")
        r=load(f)
        records=[(r["product"],{"json_pointer":"/product"})] if isinstance(r.get("product"),dict) and r.get("status")==1 else [(v,{"json_pointer":"/products/"+str(i)}) for i,v in enumerate(r.get("products",[]))]
        require(len(records)==x["products"],"OFF_SOURCE_COUNT")
        scope="off:u2c:followup_api_snapshot"
        sp={"bytes":x["bytes"],"file":x["file"],"path":str(f.relative_to(b.root)),"scope":scope,"sha256":x["sha256"],
            "snapshot_id":scope+"@sha256:"+x["sha256"],"source_role":"OFFICIAL_CURRENT_API_SAMPLE","source_url":x["url"],"version":"LOCAL_RETRIEVAL_SNAPSHOT"}
        s=common("SourceSnapshotDraft","u2c:off-snapshot:"+x["sha256"],sp,rt.clock,"REAL_DATA","REAL_SOURCE_GROUNDED",[],[],new_gov(b,domain,"LOCAL_SOURCE_BYTES_VERIFIED","OBS"))
        b.schemas.validate(s);sr=ref(s);require(sr not in new,"OFF_SNAPSHOT_DUPLICATE");new[sr]=s
        for row,locator in records:
            stats["product_records"]+=1;basis[off_basis(row)]+=1
            for pay in off_extract(row,x["sha256"],locator):
                field[pay["native_field"]]+=1
                oid="u2c:off-qualification:"+digest([s["object_id"],pay["snapshot_sha256"],pay["source_locator"],pay["native_field"]])[:40]
                q=common("OFFRecordQualification",oid,pay,rt.clock,"REAL_DATA","MIXED_CONSTRUCTED",[sr],[sr],new_gov(b,domain,"NEW_API_SOURCE_RECORD"))
                b.schemas.validate(q);qr=ref(q);require(qr not in new,"OFF_FIELD_DUPLICATE");new[qr]=q
                require(pay["effective_component_ref"]=="cc:CARBOHYDRATE_UNSPECIFIED" and pay["qualification"]=="HOLD","OFF_FIELD_PROMOTION")
    require(stats["product_records"]==a["product_records"] and field["carbohydrates-total_100g"]==a["carbohydrates_total_field_records"],"OFF_FOLLOWUP_COUNTS")
    for o in new.values():require(all(r in new for r in o["provenance_refs"]+o["dependency_refs"]),"OFF_SUPPLEMENT_CLOSURE")
    return new,{"status":"PASS_REAL_OFF_SOURCE_FIELD_SUPPLEMENT_ONLY","product_records":stats["product_records"],"basis_counts":dict(basis),"actual_field_counts":dict(field),
                "schema_validated_objects":len(new),"real_nonstandard_unit_pairs":a["real_nonstandard_unit_pairs"],
                "record_level_label_semantics_qualified":0,"measurement_conversion_qualified":0,"input_manifest_sha256":expected_sha}

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,default=Path("."));a.add_argument("--manifest",type=Path,required=True);a.add_argument("--run",type=Path,required=True)
    a.add_argument("--operation",required=True);a.add_argument("--refs",type=Path,required=True)
    x=a.parse_args()
    # Full read-only run replay before the public entry admits any purpose.
    rt,_=verify(x.root.resolve(),x.manifest.resolve(),x.run)
    ids=load(local(x.root.resolve(),x.refs))
    require(isinstance(ids,list) and all(isinstance(r,str) for r in ids),"REQUEST_REFS")
    result=Admission(rt).request(x.operation,ids);print(json.dumps(result,ensure_ascii=False))
