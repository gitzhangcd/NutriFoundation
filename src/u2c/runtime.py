#!/usr/bin/env python3
"""U2-C manifest-controlled version projections, quality ledger and consumer gate.

EXECUTE creates new outputs only. VERIFY reads existing run and original inputs;
reports may be emitted to an explicitly separate new path. Historical objects
remain immutable and are resolved by their exact legacy refs.
"""
import argparse,collections as C,csv,sys
from datetime import datetime,timezone
from core import *
from baseline import Baseline,build_manifest,local,file_check
def common(kind,oid,p,clock,source_class,instance_class,provenance,dependencies,governance,old=None):
    return seal({"object_id":oid,"kind":kind,"schema_version":VERSION,"contract_version":VERSION,
        "lifecycle":"DRAFT","producer_role":"U2C_VERSIONED_PROJECTION","created_time":clock,"clock_axis":"AUDIT_UTC",
        "provenance_refs":uniq(provenance),"dependency_refs":uniq(dependencies),"source_class":source_class,"instance_class":instance_class,
        "purpose_release_ref":pending("no research release authorized"),"purpose":"CURATION_DEV",
        "supersedes_ref":val(old) if old else na("first U2-C draft revision"),"payload":p,"governance":governance})
def new_gov(b,domains,scope,construction="DRV"):
    return {"legacy_ref":None,"legacy_schema_version":None,"stage":"U2-C","construction_class":construction,
            "verification_scope":scope,"rights_domains":sorted(set(domains)),"release_status":"HOLD","policy_version":b.policy["version"]}
def csvrows(p,header=False):
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f) if header else csv.reader(f))
class Runtime:
    def __init__(self,b):
        self.b=b;self.clock=b.manifest["audit_clock"];self.new={};self.quality={};self.q_by_measure={};self.quality_key={}
        self.qstats=C.Counter();self.offstats=C.Counter();self._gate_views={};self._family_views={}
        self.prepare_quality();self.prepare_off()
    def add_new(self,o):
        r=ref(o);require(r not in self.new,"NEW_REVISION_DUPLICATE");self.new[r]=o;return r
    def prepare_quality(self):
        b=self.b;p=b.policy["nutrition5k_quality"];threshold=Decimal(p["threshold"]);fences=b.profile["historical_expectations"]
        # Recompute every source scan total, not merely the 65 already flagged records.
        for ar,x in b.resolver.items():
            if x["namespace"]!="fallback:Nutrition5k:dish":continue
            src=file_check(b.root,x["path"],x["sha256"])
            for ri,row in enumerate(csvrows(src),1):
                require(len(row)>=p["fixed_columns"]+p["repeat_columns"] and (len(row)-p["fixed_columns"])%p["repeat_columns"]==0,"N5K_NATIVE_LAYOUT")
                ls=[row[j:j+p["repeat_columns"]] for j in range(p["fixed_columns"],len(row),p["repeat_columns"])]
                bad=False;self.qstats["dish_rows"]+=1
                for field,(a,c) in p["fields"].items():
                    total=number(row[a]);values=[number(v[c]) for v in ls]
                    require(total is not None and all(v is not None for v in values),"N5K_NUMERIC_FIELD")
                    sm=sum(values,Decimal(0));delta=abs(total-sm);st=quality_status(delta,threshold)
                    bad|=st=="HOLD_SOURCE_TOTAL_CONFLICT";self.qstats[st]+=1
                    pay={"source_artifact_ref":ar,"artifact_sha256":x["sha256"],"csv_record":ri,"field":field,"unit":p["units"][field],
                         "source_total":row[a],"ingredient_sum":str(sm),"absolute_difference":str(delta),"threshold":p["threshold"],"status":st,"policy_ref":b.policy["version"]}
                    oid="u2c:quality:"+digest([b.idx[ar]["object_id"],ri,field,p])[:40]
                    o=common("MeasurementQualityRecord",oid,pay,self.clock,"REAL_DATA","MIXED_CONSTRUCTED",[ar],[ar],new_gov(b,b.domains(ar),"SOURCE_BYTES_AND_ARITHMETIC_RECOMPUTED"))
                    r=self.add_new(o);key=(ar,ri,field);require(key not in self.quality_key,"QUALITY_KEY_DUPLICATE");self.quality_key[key]=r;self.quality[r]=o
                self.qstats["dish_rows_any_conflict"]+=bad
        # Source audit conflict list must equal independently recomputed field-level flags.
        actual={(o["payload"]["source_artifact_ref"],o["payload"]["csv_record"],o["payload"]["field"]):o["payload"] for o in self.quality.values() if o["payload"]["status"]=="HOLD_SOURCE_TOTAL_CONFLICT"}
        old=list(lines(b.input("all_conflict_flags")));oldkeys={(x["source_artifact_ref"],x["csv_record"],x["field"]) for x in old}
        require(len(oldkeys)==len(old) and set(actual)==oldkeys,"QUALITY_CONFLICT_SET_DRIFT")
        for x in old:
            a=actual[(x["source_artifact_ref"],x["csv_record"],x["field"])]
            require(number(a["source_total"])==number(x["source_total"]) and number(a["ingredient_sum"])==number(x["ingredient_sum"]) and number(a["absolute_difference"])==number(x["absolute_difference"]),"QUALITY_CONFLICT_VALUE_DRIFT")
        for o in b.by["NutrientMeasurementDraft"]:
            p=o["payload"];k=p["component_key"]
            if not self.is_n5_total(k):continue
            n=lookup(b.idx,p["native_ref"],"NativeRecord")["payload"]
            key=(n["artifact_ref"],n["locator"]["csv_record"],k.rsplit(":",1)[-1])
            require(key in self.quality_key,"QUALITY_RECORD_MISSING")
            qr=self.quality_key[key];q=self.quality[qr]["payload"]
            require(number(bound(o,"value"))==number(q["source_total"]),"QUALITY_MEASUREMENT_VALUE_DRIFT")
            self.q_by_measure[ref(o)]=qr;self.qstats["selected_total"]+=1
            self.qstats["selected_conflict"]+=q["status"]=="HOLD_SOURCE_TOTAL_CONFLICT"
        selected=list(lines(b.input("selected_quality_flags")));require(len({x["measurement_ref"] for x in selected})==len(selected) and set(self.q_by_measure)=={x["measurement_ref"] for x in selected},"QUALITY_SELECTED_SET_DRIFT")
        for x in selected:
            a=self.quality[self.q_by_measure[x["measurement_ref"]]]["payload"]
            require(a["source_artifact_ref"]==x["source_artifact_ref"] and a["csv_record"]==x["csv_record"] and a["field"]==x["field"] and a["status"]==x["flag"],"QUALITY_SELECTED_FLAG_DRIFT")
        require(self.qstats["dish_rows"]==fences["n5k_dishes"] and self.qstats["dish_rows_any_conflict"]==fences["n5k_dish_conflicts"] and self.qstats["selected_total"]==fences["selected_n5k_measurements"] and self.qstats["selected_conflict"]==fences["selected_n5k_conflicts"],"QUALITY_HISTORICAL_REGRESSION")
    @staticmethod
    def is_n5_total(key):return key.startswith("fallback:Nutrition5k:dish:") and ":ingredient:" not in key
    def prepare_off(self):
        b=self.b
        # Original product records, versioned legacy source refs and exact native locators.
        for o in b.by["ProductVersionDraft"]:
            n=lookup(b.idx,o["payload"]["native_ref"],"NativeRecord");a=lookup(b.idx,n["payload"]["artifact_ref"],"SourceArtifact")
            if not a["payload"]["namespace"].startswith("off:"):continue
            row=n["payload"]["raw"];self.offstats["historical_products"]+=1
            for pay in off_extract(row,a["payload"]["file_sha256"],n["payload"]["locator"]):
                self.add_off(pay,ref(n),ref(o),b.domains(ref(n)),"HISTORICAL_SOURCE_RECORD")
        # Newly retrieved real API samples, separate source snapshots; no claim of original-label validation.
        acquisition=load(b.input("off_acquisition"))
        for x in acquisition["attempts"]:
            if x.get("http")!=200:continue
            path=Path(b.profile["private_inputs"]["off_acquisition"]["path"]).parent/x["file"]
            fp=file_check(b.root,path,x["sha256"]);raw=load(fp)
            domain=["OFF_ODBL_REVIEW"];scope="off:u2c:bounded_api_sample"
            sp={"bytes":x["bytes"],"file":x["file"],"path":str(path),"scope":scope,"sha256":x["sha256"],
                "snapshot_id":scope+"@sha256:"+x["sha256"],"source_role":"OFFICIAL_CURRENT_API_SAMPLE","source_url":x["url"],"version":"LOCAL_RETRIEVAL_SNAPSHOT"}
            s=common("SourceSnapshotDraft","u2c:off-snapshot:"+x["sha256"],sp,self.clock,"REAL_DATA","REAL_SOURCE_GROUNDED",[],[],new_gov(b,domain,"LOCAL_SOURCE_BYTES_VERIFIED","OBS"))
            sr=self.add_new(s)
            for i,row in enumerate(raw["products"]):
                self.offstats["new_products"]+=1;self.offstats["new_basis:"+off_basis(row)]+=1
                for pay in off_extract(row,x["sha256"],{"json_pointer":"/products/"+str(i)}):
                    self.add_off(pay,sr,sr,domain,"NEW_API_SOURCE_RECORD")
        self.offstats["real_nonstandard_unit_pairs"]=acquisition["real_nonstandard_unit_pairs"]
        self.offstats["actual_total_carbohydrate_values_new"]=acquisition["carbohydrates_total_field_records"]
    def add_off(self,pay,source,dependency,domains,scope):
        self.offstats["carbohydrate_fields_interpreted"]+=1
        self.offstats["field:"+pay["native_field"]]+=1
        oid="u2c:off-qualification:"+digest([source.split("@")[0],pay["snapshot_sha256"],pay["source_locator"],pay["native_field"]])[:40]
        o=common("OFFRecordQualification",oid,pay,self.clock,"REAL_DATA","MIXED_CONSTRUCTED",[source],[source,dependency],new_gov(self.b,domains,scope))
        self.add_new(o)
    def project(self,o,validate=True):
        b=self.b;old=ref(o);k=o["kind"]
        if validate:b.validate_legacy(o)
        p=dict(o["payload"]);dd=list(o["dependency_refs"]);pp=list(o["provenance_refs"])
        domains=set(b.domains(old));stage=b.stage[old]
        scope="PINNED_LEGACY_RECORD_PROJECTION"
        if k=="AuthoritySnapshot":
            scope="LOCAL_SOURCE_BYTES_VERIFIED" if p["verification"]=="LOCAL_SOURCE_BYTES_VERIFIED" else "CLOUD_HASH_RECORDED_NOT_LOCAL_BYTES_VERIFIED"
        g={"legacy_ref":old,"legacy_schema_version":o["schema_version"],"stage":stage,"construction_class":o.get("construction_class","UNDECLARED_AT_OBJECT_LEVEL"),
            "verification_scope":scope,"rights_domains":sorted(domains),"release_status":"HOLD","policy_version":b.policy["version"]}
        if k=="MeasurementDefinition" and p["concept_key"]=="off:api_snapshot:carbohydrates":
            g["semantic_overlay"]=off_semantics("carbohydrates")
            # Correct the effective definition, but retain the declared OFF field meaning
            # and the original revision/declared component dependency.
            p["component_ref"]="cc:CARBOHYDRATE_UNSPECIFIED";p["qualification"]="HOLD_OFF_RECORD_COMPONENT_DEFINITION"
            p["blockers"]=uniq(p["blockers"]+["OFF_RECORD_COMPONENT_DEFINITION_UNVERIFIED"])
            rr=ref(b.concepts[p["component_ref"]]);dd.append(rr);domains.update(b.domains(rr))
        mref=None
        if k=="MeasurementInterpretation":
            mref=p["source_measurement_ref"];m=lookup(b.idx,mref,"NutrientMeasurementDraft")["payload"]
            if m["component_key"]=="off:api_snapshot:carbohydrates":
                g["semantic_overlay"]=off_semantics("carbohydrates");p["field_semantics_status"]="HOLD_OFF_RECORD_COMPONENT_DEFINITION"
        elif k=="NutrientMeasurementDraft":
            mref=old
            if p["component_key"]=="off:api_snapshot:carbohydrates":g["semantic_overlay"]=off_semantics("carbohydrates")
        if mref in self.q_by_measure:
            qr=self.q_by_measure[mref];q=self.quality[qr]["payload"]
            g["quality_ref"]=qr;g["quality_status"]=q["status"];dd.append(qr);domains.update(self.quality[qr]["governance"]["rights_domains"])
        if k=="ComponentConceptCandidate":
            z=lookup(b.idx,p["source_field_ref"],"ComponentNativeField")["payload"]
            g["semantic_overlay"]={"effective_component_ref":component_prior(b.policy,z["native_name"],z["native_unit"]),"source_quantity_kind":unit_kind(z["native_unit"],z["native_name"]),"measurement_equivalence":"NOT_QUALIFIED"}
        elif k=="ComponentAlignmentCandidate":
            a=lookup(b.idx,p["source_ref"],"ComponentNativeField")["payload"];t=lookup(b.idx,p["target_ref"],"ComponentNativeField")["payload"]
            x,y,u=component_kinds(b.policy,a,t);present=t.get("observed_food_nutrient_rows",0)>0
            p["unit_dimension_candidate_match"]=True if u=="SAME_DECLARED_QUANTITY_KIND" else False if u=="DIFFERENT_QUANTITY_KIND" else None
            p["target_present_in_sr_food_nutrient"]=present
            if p["unit_dimension_candidate_match"] is not True:p["review_route"]="RED";p["proposed_relation"]="AMBIGUOUS"
            g["semantic_overlay"]={"source_quantity_kind":x,"target_quantity_kind":y,"unit_relation":u,
                "value_availability":"SOURCE_VALUES_PRESENT" if present else "DICTIONARY_ONLY_NO_SOURCE_VALUES","measurement_equivalence":"NOT_QUALIFIED"}
        elif k=="AlignmentRecord":
            a=lookup(b.idx,p["source_ref"],"NativeVocabularyRecord")["payload"];t=lookup(b.idx,p["target_ref"],"NativeVocabularyRecord")["payload"]
            risk=sorted(set(p["hard_conflicts"]+conflicts(a["native_label"],t["native_label"])+conflicts(p["query_form"],p["matched_target_form"])))
            flags=[]
            if risk:flags.append("EXPLICIT_STATE_CONFLICT_CANDIDATE");p["review_route"]="RED";p["proposed_relation"]="AMBIGUOUS"
            if p["ranking_score"]>=0.9:flags.append("HIGH_LEXICAL_SCORE_REVIEW")
            if not qualifiers(a["native_label"]) or not qualifiers(t["native_label"]):flags.append("STATE_DIMENSION_UNRESOLVED")
            g["candidate_risk"]={"flags":flags,"rule_version":b.policy["version"],"legacy_review_route":o["payload"]["review_route"]}
            p["hard_conflicts"]=risk
        g["rights_domains"]=sorted(domains)
        x=common(k,o["object_id"],p,self.clock,o["source_class"],o["instance_class"],pp,dd,g,old)
        if validate:self.validate_current(x)
        return x
    def validate_current(self,o):
        self.b.schemas.validate(o);g=o["governance"];k=o["kind"]
        for rr in o["dependency_refs"]+o["provenance_refs"]:
            require(rr in self.b.idx or rr in self.new,"CURRENT_REFERENCE_MISSING")
        if g["legacy_ref"] is not None:
            old=lookup(self.b.idx,g["legacy_ref"])
            require(o["object_id"]==old["object_id"] and o["supersedes_ref"]==val(ref(old)),"PROJECTION_LEGACY_IDENTITY")
        else:require(o["supersedes_ref"]["tag"]=="NOT_APPLICABLE","NEW_OBJECT_SUPERSESSION")
        if "quality_ref" in g:
            r=g["quality_ref"];require(r in self.quality and r in o["dependency_refs"] and self.quality[r]["payload"]["status"]==g["quality_status"],"QUALITY_DEPENDENCY_MISMATCH")
        if k=="MeasurementQualityRecord":
            p=o["payload"];a=lookup(self.b.idx,p["source_artifact_ref"],"SourceArtifact")
            require(p["artifact_sha256"]==a["payload"]["file_sha256"] and p["source_artifact_ref"] in o["dependency_refs"],"QUALITY_SOURCE_IDENTITY")
            d=abs(number(p["source_total"])-number(p["ingredient_sum"]))
            require(d==number(p["absolute_difference"]) and p["status"]==quality_status(d,number(p["threshold"])),"QUALITY_RECORD_DRIFT")
        if k=="SourceFamily":self.b.family_guard(lookup(self.b.idx,g["legacy_ref"]))
        return True
    def retain(self,x):
        k=x["kind"];g=x["governance"];old=g["legacy_ref"]
        if k=="MeasurementInterpretation":self._gate_views[x["payload"]["source_measurement_ref"]]=x
        elif k=="SourceFamily":self._family_views[old]=x
    def decision(self,operation,refs):
        """Actual local consumer entry. Resolve refs from validated store, never accept
        caller assertions of quality, independence or release. All nonactivated operations deny.
        """
        rules=self.b.policy["operation_policy"];require(operation in rules,"OPERATION_UNREGISTERED")
        if rules[operation]=="NOT_IMPLEMENTED_DENY":return {"decision":"HOLD","reason":"TASK_NOT_IMPLEMENTED_OR_AUTHORIZED"}
        if operation in ("inspect","candidate_inspect"):
            require(bool(refs) and all(r in self.b.idx for r in refs),"CURATION_REFERENCE_MISSING")
            for r in refs:
                o=self.b.idx[r];self.b.validate_legacy(o)
                if operation=="candidate_inspect":require(o["kind"] in ("AlignmentRecord","ComponentAlignmentCandidate","ComponentConceptCandidate"),"REF_KIND_MISMATCH")
            return {"decision":"ALLOW","reason":"CURATION_DEV_STRUCTURAL_INSPECTION_ONLY"}
        if operation=="physical_identity":return {"decision":"HOLD","reason":"INSTANCE_EQUIVALENCE_NOT_AUTHORIZED"}
        if operation=="independent_evidence_count":
            try:
                require(bool(refs) and all(r in self._family_views for r in refs),"SOURCE_FAMILY_MISSING")
                independence_guard([self._family_views[r]["payload"] for r in refs])
            except ContractError as e:return {"decision":"HOLD","reason":str(e)}
            # No qualified independence adjudication is activated.
            return {"decision":"HOLD","reason":"INDEPENDENCE_REFERENCE_NOT_ACTIVATED"}
        if operation=="measurement_calculate":
            require(len(refs)==1,"MEASUREMENT_REQUEST_GRAIN");r=refs[0]
            if r not in self._gate_views:return {"decision":"HOLD","reason":"MEASUREMENT_INTERPRETATION_MISSING"}
            x=self._gate_views[r];p=x["payload"];g=x["governance"];m=lookup(self.b.idx,r,"NutrientMeasurementDraft")
            if self.is_n5_total(m["payload"]["component_key"]):
                qref=self.q_by_measure.get(r)
                if not qref or qref not in self.quality or g.get("quality_ref")!=qref or qref not in x["dependency_refs"]:
                    return {"decision":"HOLD","reason":"QUALITY_RECORD_MISSING_OR_UNBOUND"}
                q=self.quality[qref]["payload"];status=q["status"]
                if g.get("quality_status")!=status:return {"decision":"HOLD","reason":"QUALITY_RECORD_MISSING_OR_UNBOUND"}
                if status=="HOLD_SOURCE_TOTAL_CONFLICT":return {"decision":"HOLD","reason":status}
                if status!="WITHIN_EXPLORATORY_TOLERANCE_NOT_QUALIFIED":return {"decision":"HOLD","reason":"QUALITY_RECORD_UNRESOLVED"}
            if g.get("semantic_overlay",{}).get("record_definition_status")=="PENDING_ORIGINAL_LABEL_AND_TRANSFORMATION":
                return {"decision":"HOLD","reason":"OFF_RECORD_COMPONENT_DEFINITION_UNRESOLVED"}
            if p["qualification"]!="SCIENCE_CALCULATION_QUALIFIED" or p["normalized_food_value"]["tag"]!="VALUE":
                return {"decision":"HOLD","reason":"MEASUREMENT_NOT_QUALIFIED"}
            # A draft view cannot mint release/measurement qualifications.
            return {"decision":"HOLD","reason":"CALCULATION_TASK_RELEASE_NOT_ACTIVATED"}
        raise ContractError("OPERATION_NOT_IMPLEMENTED")
def partition(o):
    d=o["governance"]["rights_domains"]
    return d[0] if len(d)==1 else "MIXED_RESTRICTED_"+digest(d)[:16]
def out_safe(root,out,existing=False):
    root=root.resolve();out=out.resolve()
    require(out.is_relative_to(root/"runs/B1/U2-C") and (out.is_dir() if existing else not out.exists()),"OUTPUT_MUST_BE_NEW_U2C_RUN")
    return out
def summarize(rt,counts,parts):
    b=rt.b;gate=C.Counter()
    for r in rt._gate_views:
        z=rt.decision("measurement_calculate",[r]);gate[(z["decision"],z["reason"])]+=1
    require(sum(v for (d,k),v in gate.items() if d=="ALLOW")==0,"UNEXPECTED_SCIENTIFIC_ADMISSION")
    return {"status":"PASS_BOUNDED_U2C_PROJECTION_AND_ADMISSION","legacy_objects":len(b.idx),"legacy_kinds":len(b.by),
            "source_stage_counts":b.source_counts,"new_objects":len(rt.new),"object_count":sum(counts.values()),"typed_kinds":dict(counts),
            "rights_partitions":len(parts),"partition_counts":dict(parts),"quality":dict(rt.qstats),"off":dict(rt.offstats),
            "actual_measurement_gate_requests":len(rt._gate_views),"gate_results":[{"decision":d,"reason":k,"count":v} for (d,k),v in sorted(gate.items())],
            "research_measurements_qualified":0,"mapping_releases":0,"scientific_releases":0,"global_b1_frozen":False,"global_u3_frozen":False}
def execute(root,manifest_path,out):
    out=out_safe(root,out);b=Baseline(root,load(manifest_path));rt=Runtime(b)
    # No old output paths are touched. Incomplete new runs have no success receipt.
    out.mkdir(parents=True);priv=out/"private";priv.mkdir();tree=priv/"typed_partitions";tree.mkdir()
    handles={};counts=C.Counter();parts=C.Counter();filecounts=C.Counter();risk=C.Counter();component=C.Counter();verification=C.Counter()
    def write(o):
        k=o["kind"];d=partition(o);rel=d+"/"+k+".jsonl"
        if rel not in handles:
            path=tree/rel;path.parent.mkdir(parents=True,exist_ok=True);handles[rel]=path.open("x",encoding="utf8")
        handles[rel].write(canon(o)+"\n");filecounts[rel]+=1;counts[k]+=1;parts[d]+=1
        rt.retain(o)
        if k=="AuthoritySnapshot":verification[o["governance"]["verification_scope"]]+=1
        if k=="AlignmentRecord":risk[(o["payload"]["review_route"],o["governance"]["candidate_risk"]["legacy_review_route"])]+=1
        if k=="ComponentAlignmentCandidate":component[(o["payload"]["review_route"],o["governance"]["semantic_overlay"]["unit_relation"],o["governance"]["semantic_overlay"]["value_availability"])]+=1
    try:
        for n,o in enumerate(b.idx.values(),1):
            x=rt.project(o);write(x)
            if n%50000==0:print("PROJECTED_AND_SCHEMA_VALIDATED",n,flush=True)
        for o in rt.new.values():rt.validate_current(o);write(o)
    finally:
        for h in handles.values():h.close()
    manifest={k:{"rows":v,"bytes":(tree/k).stat().st_size,"sha256":sha(tree/k)} for k,v in filecounts.items()}
    put(priv/"partition_manifest.json",manifest)
    b.verify_files()
    report=summarize(rt,counts,parts);report.update({"manifest_sha256":sha(manifest_path),"schema_sha256":sha(root/b.manifest["schema_path"]),"schema_validator":"jsonschema Draft202012Validator",
        "schema_validated_objects":sum(counts.values()),"candidate_risk_route_changes":[{"new":k[0],"legacy":k[1],"count":v} for k,v in sorted(risk.items())],
        "component_route_counts":[{"route":k[0],"unit_relation":k[1],"value_availability":k[2],"count":v} for k,v in sorted(component.items())],
        "authority_verification_counts":dict(verification),"input_files_unchanged":True,"partition_manifest_sha256":sha(priv/"partition_manifest.json")})
    put(out/"U2CExecutionReport.json",report);print(json.dumps(report,ensure_ascii=False),flush=True)
def verify(root,manifest_path,run,report_path=None):
    run=out_safe(root,run,True)
    if report_path is not None:
        report_path=report_path.resolve();require(not report_path.exists() and not report_path.is_relative_to(run) and report_path.is_relative_to(root.resolve()/"runs/B1/U2-C"),"VERIFY_REPORT_MUST_BE_SEPARATE")
    b=Baseline(root,load(manifest_path));rt=Runtime(b);prior=load(run/"U2CExecutionReport.json")
    require(prior["manifest_sha256"]==sha(manifest_path),"RUN_MANIFEST_IDENTITY")
    mp=run/"private/partition_manifest.json";require(sha(mp)==prior["partition_manifest_sha256"],"PARTITION_MANIFEST_DRIFT")
    m=load(mp);tree=run/"private/typed_partitions";require(set(m)=={str(p.relative_to(tree)) for p in tree.rglob("*.jsonl")},"PARTITION_FILE_SET")
    seen=set();seen_new=set();counts=C.Counter();parts=C.Counter()
    for rel,x in sorted(m.items()):
        p=local(tree.resolve(),rel);require(p.stat().st_size==x["bytes"] and sha(p)==x["sha256"],"PARTITION_HASH")
        n=0
        for o in lines(p):
            g=o["governance"];old=g["legacy_ref"];k=o["kind"];d=partition(o)
            require(rel==d+"/"+k+".jsonl","RIGHTS_OR_TYPE_PARTITION_MISMATCH")
            if old is None:
                r=ref(o);require(r in rt.new and r not in seen_new,"NEW_OBJECT_REPLAY")
                expected=rt.new[r];seen_new.add(r)
            else:
                require(old in b.idx and old not in seen,"LEGACY_REPLAY_CLOSURE")
                expected=rt.project(b.idx[old],validate=False);seen.add(old)
            require(canon(o)==canon(expected),"CURRENT_PROJECTION_REPLAY_DRIFT")
            revision_ok(o);rt.retain(o);counts[k]+=1;parts[d]+=1;n+=1
        require(n==x["rows"],"PARTITION_COUNT")
    require(seen==set(b.idx) and seen_new==set(rt.new),"PROJECTION_COMPLETENESS")
    b.verify_files()
    report=summarize(rt,counts,parts);report.update({"status":"PASS_READ_ONLY_FULL_PROJECTION_REPLAY","replayed_legacy_objects":len(seen),"replayed_new_objects":len(seen_new),"all_replayed":len(seen)+len(seen_new),"schema_check_basis":"byte-semantic equality with full schema-validated execution outputs","input_files_unchanged":True,"run_unchanged":True})
    if report_path is not None:put(report_path,report)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    return rt,report
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--root",type=Path,default=Path("."));sp=a.add_subparsers(dest="command",required=True)
    f=sp.add_parser("freeze");f.add_argument("--profile",type=Path,required=True);f.add_argument("--manifest",type=Path,required=True)
    e=sp.add_parser("execute");e.add_argument("--manifest",type=Path,required=True);e.add_argument("--out",type=Path,required=True)
    v=sp.add_parser("verify");v.add_argument("--manifest",type=Path,required=True);v.add_argument("--run",type=Path,required=True);v.add_argument("--report",type=Path)
    x=a.parse_args();root=x.root.resolve()
    if x.command=="freeze":
        require(not x.manifest.exists() and x.manifest.resolve().is_relative_to(root/"runs/B1/U2-C"),"MANIFEST_PATH")
        m=build_manifest(root,x.profile,x.manifest);print("PINNED_INPUTS",len(m["files"]))
    elif x.command=="execute":execute(root,x.manifest.resolve(),x.out)
    else:verify(root,x.manifest.resolve(),x.run,x.report)
