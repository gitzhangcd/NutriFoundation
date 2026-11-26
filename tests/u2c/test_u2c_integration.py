#!/usr/bin/env python3
"""Final U2-C integration verification against the persisted full real projection.
Reports only aggregate checks. A separate new validation directory is required.
"""
import argparse,copy,collections as C,sys,pathlib as P
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/u2c"))
from core import *
from runtime import verify,partition
from admission import Admission,supplement_off
from review_audit import audit_queue

def main(root,manifest,run,out,followup,followup_sha,queues,regression):
    root=root.resolve();out=out.resolve();run=run.resolve()
    require(out.is_relative_to(root/"runs/B1/U2-C") and not out.exists() and not out.is_relative_to(run),"NEW_VALIDATION_DIRECTORY_REQUIRED")
    fences={str(p.resolve()):sha(p) for p in [manifest,run/"U2CExecutionReport.json",run/"private/partition_manifest.json",followup,regression]+queues}
    rt,replay=verify(root,manifest.resolve(),run)
    a=Admission(rt);b=rt.b;tests=[]
    def pos(name,fn):
        try:require(fn() is not False,"POSITIVE_ASSERTION");tests.append({"test":name,"expected":"ACCEPT","actual":"ACCEPT","pass":True})
        except Exception as e:tests.append({"test":name,"expected":"ACCEPT","actual":type(e).__name__+":"+str(e)[:150],"pass":False})
    def neg(name,code,fn):
        try:fn();tests.append({"test":name,"expected":code,"actual":"ACCEPT","pass":False})
        except ContractError as e:tests.append({"test":name,"expected":code,"actual":str(e),"pass":str(e).startswith(code)})
        except Exception as e:tests.append({"test":name,"expected":code,"actual":type(e).__name__+":"+str(e)[:150],"pass":False})
    def hold(name,code,fn):
        try:
            d=fn();ok=d["decision"]=="HOLD" and d["reason"]==code
            tests.append({"test":name,"expected":code,"actual":d["reason"] if d["decision"]=="HOLD" else "ALLOW","pass":ok})
        except Exception as e:tests.append({"test":name,"expected":code,"actual":type(e).__name__+":"+str(e)[:150],"pass":False})
    def mutate(o,fn):z=copy.deepcopy(o);fn(z);return seal(z)
    def first(k,cond=lambda x:True):return next(o for o in b.by[k] if cond(o))
    family=first("SourceFamily")
    family2=first("SourceFamily",lambda x:x["payload"]["carrier_scope"]!=family["payload"]["carrier_scope"])
    binding=first("SourceFamilyBinding",lambda x:x["payload"]["source_family_ref"]==ref(family))
    prior=first("ComponentConceptCandidate",lambda x:x["payload"]["declared_label"]=="维生素A")
    edge=first("AlignmentRecord")
    component=first("ComponentAlignmentCandidate")
    projected={k:a.view(ref(o)) for k,o in [("family",family),("binding",binding),("prior",prior),("edge",edge),("component",component)]}
    pos("full 40-kind historical projection replay, new 2 kinds",lambda:replay["all_replayed"]==replay["legacy_objects"]+replay["new_objects"] and replay["legacy_kinds"]==len(b.schemas.kinds)-2)
    pos("current record accepted only through version-bound projection",lambda:a.projection(projected["edge"]))
    pos("real candidate inspection through consumer entry",lambda:a.request("candidate_inspect",[ref(edge)])["decision"]=="ALLOW")
    pos("real authority scopes distinguish bytes from cloud hash",lambda:sum(a.view(ref(o))["governance"]["verification_scope"]=="CLOUD_HASH_RECORDED_NOT_LOCAL_BYTES_VERIFIED" for o in b.by["AuthoritySnapshot"])==2)
    neg("audit mutation 1: fabricated family independence resealed","FAMILY_INDEPENDENCE_UNQUALIFIED",
        lambda:b.validate_legacy(mutate(family,lambda z:z["payload"].update(independence_status="INDEPENDENCE_VERIFIED_FOR_TASK",independent_measurement_claim=True))))
    def wrong_binding(z):
        z["payload"]["source_family_ref"]=ref(family2)
        z["dependency_refs"]=[ref(family2) if x==ref(family) else x for x in z["dependency_refs"]]
    neg("audit mutation 2: wrong family carrier resealed","FAMILY_CARRIER_MISMATCH",lambda:b.validate_legacy(mutate(binding,wrong_binding)))
    neg("audit mutation 3: actual RAE prior replaced with RE resealed","COMPONENT_PRIOR_UNIT_MISMATCH",
        lambda:b.validate_legacy(mutate(prior,lambda z:z["payload"].update(prior_u2b_component_id="cc:VITAMIN_A_RE"))))
    neg("audit mutation 4: extra field in actual projected candidate resealed","SCHEMA_additionalProperties",
        lambda:a.projection(mutate(projected["edge"],lambda z:z["payload"].update(unregistered_field=True))))
    neg("audit mutation 5: required source endpoint removed resealed","REQUIRED_DEPENDENCY_MISSING",
        lambda:b.validate_legacy(mutate(edge,lambda z:z.update(dependency_refs=[x for x in z["dependency_refs"] if x!=z["payload"]["source_ref"]]))))
    # New projection endpoint itself is fail closed, even for schema-valid modifications.
    neg("projected family forged independent","SCHEMA_",lambda:a.projection(mutate(projected["family"],lambda z:z["payload"].update(independent_measurement_claim=True))))
    neg("projected family carrier swapped","CURRENT_PROJECTION_NOT_AUTHORIZED",lambda:a.projection(mutate(projected["binding"],wrong_binding)))
    neg("projected prior changed to RE","CURRENT_PROJECTION_NOT_AUTHORIZED",lambda:a.projection(mutate(projected["prior"],lambda z:z["payload"].update(prior_u2b_component_id="cc:VITAMIN_A_RE"))))
    neg("projected candidate dependency removed","CURRENT_PROJECTION_NOT_AUTHORIZED",lambda:a.projection(mutate(projected["edge"],lambda z:z.update(dependency_refs=[x for x in z["dependency_refs"] if x!=z["payload"]["source_ref"]]))))
    neg("projected mapping promoted EXACT","SCHEMA_",lambda:a.projection(mutate(projected["edge"],lambda z:z["payload"].update(relation_type="EXACT",accepted_equivalence=True))))
    neg("projected candidate scientific release","SCHEMA_",lambda:a.projection(mutate(projected["edge"],lambda z:z.update(purpose="TRAIN"))))
    neg("projected rights domain omitted","CURRENT_PROJECTION_NOT_AUTHORIZED",lambda:a.projection(mutate(projected["edge"],lambda z:z["governance"].update(rights_domains=["USDA_PUBLIC_DOMAIN_CANDIDATE"]))))
    neg("boolean rank rejected by standard schema","SCHEMA_",lambda:a.projection(mutate(projected["edge"],lambda z:z["payload"].update(rank=True))))
    neg("numeric score outside permitted range","SCHEMA_",lambda:a.projection(mutate(projected["edge"],lambda z:z["payload"].update(ranking_score=1.2))))
    neg("unverified normalized nutrient value injected","CURRENT_PROJECTION_NOT_AUTHORIZED",
        lambda:a.projection(mutate(a.view(ref(first("MeasurementInterpretation"))),lambda z:z["payload"].update(normalized_food_value=val("100")))))
    # Real consumer gate requests for every selected measurement.
    gate=C.Counter()
    for r in rt._gate_views:
        z=a.request("measurement_calculate",[r]);gate[(z["decision"],z["reason"])]+=1
    pos("all real measurement requests remain held",lambda:sum(gate.values())==len(rt._gate_views) and all(k[0]=="HOLD" for k in gate))
    pos("all actual selected Nutrition5k conflicts explicitly blocked",lambda:gate[("HOLD","HOLD_SOURCE_TOTAL_CONFLICT")]==rt.qstats["selected_conflict"])
    pos("OFF historical carbohydrates blocked for record-level semantic uncertainty",lambda:gate[("HOLD","OFF_RECORD_COMPONENT_DEFINITION_UNRESOLVED")]>0)
    mr=next(r for r,q in rt.q_by_measure.items() if rt.quality[q]["payload"]["status"]=="HOLD_SOURCE_TOTAL_CONFLICT")
    qr=rt.q_by_measure[mr];view=rt._gate_views[mr]
    hold("actual conflict measurement request","HOLD_SOURCE_TOTAL_CONFLICT",lambda:a.request("measurement_calculate",[mr]))
    rt.q_by_measure.pop(mr)
    try:hold("missing quality record fails closed","QUALITY_RECORD_MISSING_OR_UNBOUND",lambda:a.request("measurement_calculate",[mr]))
    finally:rt.q_by_measure[mr]=qr
    rt._gate_views[mr]=mutate(view,lambda z:z.update(dependency_refs=[r for r in z["dependency_refs"] if r!=qr]))
    try:hold("missing quality dependency fails closed","QUALITY_RECORD_MISSING_OR_UNBOUND",lambda:a.request("measurement_calculate",[mr]))
    finally:rt._gate_views[mr]=view
    rt._gate_views.pop(mr)
    try:hold("missing interpretation fails closed","MEASUREMENT_INTERPRETATION_MISSING",lambda:a.request("measurement_calculate",[mr]))
    finally:rt._gate_views[mr]=view
    hold("unknown source families cannot count as independent","INDEPENDENCE_NOT_QUALIFIED",lambda:a.request("independent_evidence_count",[ref(family),ref(family2)]))
    hold("physical identity never promoted by candidate","INSTANCE_EQUIVALENCE_NOT_AUTHORIZED",lambda:a.request("physical_identity",[ref(edge)]))
    for op,rule in sorted(b.policy["operation_policy"].items()):
        if rule=="NOT_IMPLEMENTED_DENY":
            hold("unactivated entry denied: "+op,"TASK_NOT_IMPLEMENTED_OR_AUTHORIZED",lambda op=op:a.request(op,[ref(edge)]))
    # Real source component IDs and semantic types, separate value availability.
    e_rows=[]
    for o in b.by["ComponentAlignmentCandidate"]:
        t=b.idx[o["payload"]["target_ref"]]["payload"]
        if t["native_id"]=="1158":
            x=a.view(ref(o));e_rows.append(x)
    pos("actual FDC 1158 vitamin E dictionary-only, not chemical alpha-tocopherol",lambda:bool(e_rows) and all(x["governance"]["semantic_overlay"]["source_quantity_kind"]==x["governance"]["semantic_overlay"]["target_quantity_kind"]=="ALPHA_TE" and x["governance"]["semantic_overlay"]["value_availability"]=="DICTIONARY_ONLY_NO_SOURCE_VALUES" for x in e_rows))
    pos("actual vitamin A RAE source anchored",lambda:projected["prior"]["governance"]["semantic_overlay"]["effective_component_ref"]=="cc:VITAMIN_A_RAE")
    pos("RE and RAE distinct",lambda:unit_kind("μg RE")=="RE" and unit_kind("μg RAE")=="RAE" and component_prior(b.policy,"维生素A","μg RE")=="cc:VITAMIN_A_RE")
    pos("all bogus unknown unit words remain unknown",lambda:all(unit_kind(u) is None for u in ("FREE","PURE","SCORE","unknown-A","unknown-B")) and unit_relation(unit_kind("unknown-A"),unit_kind("unknown-B"))=="UNRESOLVED")
    neg("unknown unit pair not admitted as equal","COMPONENT_QUANTITY_KIND_UNQUALIFIED",lambda:exact_component_guard(None,None))
    neg("RE and RAE not equal","COMPONENT_QUANTITY_KIND_UNQUALIFIED",lambda:exact_component_guard("RAE","RE"))
    neg("alpha-tocopherol mass not alpha-TE","COMPONENT_QUANTITY_KIND_UNQUALIFIED",lambda:exact_component_guard("ALPHA_TE","MASS"))
    neg("100mL/100g without density","DENSITY_REQUIRED",lambda:compatible_basis("PER_100G","PER_100ML","RAW","RAW"))
    neg("serving mass absent","PORTION_MASS_REQUIRED",lambda:compatible_basis("PER_SERVING","PER_100G","RAW","RAW"))
    neg("unknown food state","FOOD_STATE_UNQUALIFIED",lambda:compatible_basis("PER_100G","PER_100G",None,None))
    pos("Chinese cooking/frozen conflicts now detected",lambda:all(conflicts(x,y) for x,y in [("生鸡肉","cooked chicken"),("红烧肉","raw pork"),("卤牛肉","raw beef"),("烤鸡","raw chicken"),("冻鱼","fresh fish")]))
    pos("Chinese lexical false positive guards",lambda:"raw" not in qualifiers("花生") and "raw" not in qualifiers("生菜"))
    # Explicit policy registration for a synthetic new adapter, not real-source admission.
    pc=copy.deepcopy(b.policy);pc["recipe_rules"].append({"source_namespace":"synthetic:recipe","parent_namespace":"synthetic:ingredient","source_kind":"RecipeIngredientDraft","parent_kind":"FoodEntityDraft","quantity_policy":"PENDING_UNIT_AND_BASIS","child_key":"ingredient_id","parent_key":"business_id","crosscheck_key":"code","transform":"EXACT_TEXT"})
    pos("new recipe rule can be selected without core edit",lambda:recipe_policy(pc,"synthetic:recipe","synthetic:ingredient")["transform"]=="EXACT_TEXT")
    neg("unregistered new source rule rejected","RECIPE_POLICY_UNREGISTERED",lambda:recipe_policy(b.policy,"synthetic:recipe","synthetic:ingredient"))
    neg("wrong link policy endpoint rejected","SOURCE_LINK_POLICY_UNREGISTERED",lambda:link_policy(b.policy,"fallback:Nutrition5k:dish","nutridata:ingredient","FoodInstanceDraft","FoodEntityDraft"))
    # Two explicit audit clocks, stable logical ID and separate revision. Bounded test, not full re-execution.
    prev=rt.clock;z=a.view(ref(edge))
    try:
        rt.clock="2027-01-01T00:00:00+00:00";later=rt.project(edge)
        pos("stable object id across explicit audit clocks",lambda:z["object_id"]==later["object_id"] and z["revision_id"]!=later["revision_id"])
    finally:rt.clock=prev
    # Targeted new actual OFF product supplement (includes both carbohydrate field names).
    new,off=supplement_off(rt,followup.relative_to(root),followup_sha)
    pos("actual OFF total-carbohydrate fields retained",lambda:off["actual_field_counts"].get("carbohydrates-total_100g",0)>0 and all(o["payload"]["effective_component_ref"]=="cc:CARBOHYDRATE_UNSPECIFIED" for o in new.values() if o["kind"]=="OFFRecordQualification"))
    # Frozen source-only review packets remain unchanged. Audit all 17k persisted edges.
    q=audit_queue(rt,run,queues);q2=audit_queue(rt,run,queues)
    pos("generic read-only review audit reentrant without overwriting any run",lambda:canon(q)==canon(q2))
    pos("rule red coverage rescreen has more candidates than historical",lambda:q["new_rule_red_sources"]>=q["previous_rule_red_sources"])
    historical=load(regression)
    pos("historical regression 141/141 and D0 770 inverse",lambda:historical["status"]=="PASS_HISTORICAL_NON_REGRESSION" and historical["passed"]==historical["total"] and historical["historical_tests"]["D0"]["exact_bridge_roundtrip"]==770)
    require(all(sha(P.Path(p))==v for p,v in fences.items()),"FINAL_INPUT_MUTATION")
    b.verify_files()
    out.mkdir(parents=True);private=out/"private";private.mkdir();d=private/"OFF_ODBL_REVIEW";d.mkdir()
    for k in sorted({o["kind"] for o in new.values()}):
        with (d/(k+".jsonl")).open("x",encoding="utf8") as f:
            for o in new.values():
                if o["kind"]==k:f.write(canon(o)+"\n")
    put(private/"off_supplement_manifest.json",{p.name:{"sha256":sha(p),"bytes":p.stat().st_size} for p in d.glob("*.jsonl")})
    put(out/"ReadOnlyReplayReport.json",replay);put(out/"OFFFollowupReport.json",off);put(out/"ReviewRiskAudit.json",q)
    result={"status":"PASS_U2C_INTEGRATION" if all(x["pass"] for x in tests) else "FAIL_U2C_INTEGRATION","tests":tests,
       "total":len(tests),"passed":sum(x["pass"] for x in tests),"failed":sum(not x["pass"] for x in tests),"actual_measurement_requests":sum(gate.values()),
       "actual_measurement_gate_counts":[{"decision":d,"reason":k,"count":v} for (d,k),v in sorted(gate.items())],
       "historical_tests_passed":historical["passed"],"historical_tests_total":historical["total"],"schema_and_replay_objects":replay["all_replayed"],
       "followup_schema_objects":off["schema_validated_objects"],"new_science_qualification":0,"release_count":0,"input_fences_unchanged":True,
       "guard_scope":"real projected measurement and evidence admissions; unactivated geometry/intake/reference/probe/training/publish operations deny; no future production consumer claimed",
       "limitations":["no discriminating real OFF nonstandard-unit pair in bounded attempts","new source raw parser and production calculation/evidence/geometry consumers not implemented","no true blind access control or independent Critic judgment","risk screening only on persisted candidates, not omitted retrieval pool"]}
    put(out/"U2CIntegrationReport.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!="tests"},ensure_ascii=False),flush=True)
    for x in tests:
        if not x["pass"]:print("FAIL",x,flush=True)
    require(result["failed"]==0,"U2C_INTEGRATION_TEST_FAILURE")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--manifest",type=P.Path,required=True);p.add_argument("--run",type=P.Path,required=True);p.add_argument("--out",type=P.Path,required=True)
    p.add_argument("--followup",type=P.Path,required=True);p.add_argument("--followup-sha",required=True);p.add_argument("--queue",type=P.Path,action="append",required=True);p.add_argument("--regression",type=P.Path,required=True)
    a=p.parse_args();main(a.root,a.manifest,a.run,a.out,a.followup.resolve(),a.followup_sha,a.queue,a.regression)
