#!/usr/bin/env python3
"""Deterministic positive and negative contract tests, plus mutation tests on real private objects.
Synthetic rule inputs are tests, never admitted research records. No raw records in output.
"""
import argparse, copy, json, pathlib as P, sys
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/b1"))
# Also works at repository scripts/udf/b1 and from tests/udf/b1.
sys.path.insert(0,str(P.Path(__file__).resolve().parents[3]/"scripts/udf/b1") if len(P.Path(__file__).resolve().parents)>3 else "")
from contract import *
from run_b1 import read_back,atomic_json

def test(run,out):
    objs=read_back(run/"private/typed_collections")
    idx=validate_set(objs);bykind={}
    for o in objs:bykind.setdefault(o["kind"],[]).append(o)
    result=[]
    def positive(name,fn):
        try:fn();result.append({"name":name,"expected":"ACCEPT","observed":"ACCEPT","pass":True})
        except Exception as e:result.append({"name":name,"expected":"ACCEPT","observed":type(e).__name__+":"+str(e)[:120],"pass":False})
    def neg(name,code,fn):
        try:fn();result.append({"name":name,"expected":code,"observed":"ACCEPT","pass":False})
        except ContractError as e:result.append({"name":name,"expected":code,"observed":str(e),"pass":str(e)==code})
        except Exception as e:result.append({"name":name,"expected":code,"observed":type(e).__name__+":"+str(e)[:120],"pass":False})
    def seal(o):
        o.pop("revision_id",None);o["revision_id"]=digest(o);return o
    def closure(o,extra=()):
        seen={}
        def add(r):
            if r in seen:return
            x=idx[r];seen[r]=x
            for rr in x["provenance_refs"]+x["dependency_refs"]:add(rr)
        for r in o["provenance_refs"]+o["dependency_refs"]+list(extra):add(r)
        return list(seen.values())
    def mutate(o,fn,extra=(),reseal=True):
        z=copy.deepcopy(o);fn(z)
        if reseal:seal(z)
        return validate_set(closure(o,extra)+[z])
    def first(k,cond=lambda x:True):return next(o for o in bykind[k] if cond(o))
    nr=first("NativeRecord")
    m=first("NutrientMeasurementDraft",lambda x:x["payload"]["reference_profile"]=="Q-COMPOSITION_SOURCE_UNQUALIFIED")
    tr=first("NutrientMeasurementDraft",lambda x:isinstance(x["payload"]["bindings"]["value"]["raw_value"],str) and x["payload"]["bindings"]["value"]["raw_value"].strip().lower()=="tr")
    r=first("RecipeIngredientDraft",lambda x:x["payload"]["parent_ref"]["tag"]=="VALUE")
    hold=first("RecipeIngredientDraft",lambda x:x["payload"]["link_status"]=="HOLD_UNMATCHED_OR_CONFLICT")
    d=first("DietaryObservationDraft");qa=first("QARecordDraft");link=first("NativeLinkDraft")
    art=first("SourceArtifact")
    positive("real private typed collections validate",lambda:validate_set(objs))
    positive("lexical zero remains value; unknown Tr is not zero",lambda:require(raw_numeric_slot("0")==slot_value("0") and raw_numeric_slot("Tr")["tag"]=="PENDING","TOKEN_SEMANTICS"))
    positive("source-native pending orphan retained",lambda:require(hold["payload"]["parent_ref"]["tag"]=="PENDING","ORPHAN_NOT_RETAINED"))
    positive("structural allowlist projection",lambda:validate_dev_projection(dev_projection(qa)))
    positive("all current real records restricted to curation",lambda:[require_release(x,"CURATION_DEV") for x in objs])
    positive("valid explicit unit/state comparison guard",lambda:conversion_guard("mL","g","RAW","RAW",density=1.0))
    positive("native link evidence can be structural candidate",lambda:validate_relation("NATIVE_CANDIDATE_LINK","left","right",True,"BUSINESS_ID_CODE"))
    neg("same-name recipe and image promoted to instance","INSTANCE_IDENTITY_NOT_PROVED",lambda:validate_relation("SAME_PHYSICAL_INSTANCE","recipe","image",False,"SAME_NAME"))
    neg("perceptual hash similarity promoted to instance","INSTANCE_IDENTITY_NOT_PROVED",lambda:validate_relation("SAME_PHYSICAL_INSTANCE","image1","image2",True,"PHASH_SIMILAR"))
    neg("unknown or missing numeric slot with hidden value","SLOT_UNAVAILABLE_INVALID",lambda:validate_slot({"tag":"UNAVAILABLE","reason":"UNKNOWN","detail":"hidden","value":0}))
    neg("Tr silently changed to measured zero","MEASUREMENT_VALUE_DRIFT",lambda:mutate(tr,lambda z:z["payload"].update(original_value=slot_value("0"))))
    neg("unmarked oil given arbitrary default amount","RECIPE_QUANTITY_DRIFT",lambda:mutate(r,lambda z:z["payload"].update(quantity=slot_value("0"))))
    neg("unqualified recipe note converted to grams","RECIPE_NOTE_UNIT_BASIS_HOLD",lambda:mutate(r,lambda z:z["payload"].update(unit=slot_value("g"))))
    neg("raw and cooked values compared as equal","FOOD_STATE_INCOMPARABLE",lambda:conversion_guard("g","g","RAW","COOKED"))
    neg("mL to g without density","DENSITY_REQUIRED",lambda:conversion_guard("mL","g","RAW","RAW"))
    neg("serving to g without portion mass","PORTION_MASS_REQUIRED",lambda:conversion_guard("serving","g","RAW","RAW"))
    neg("same source family double counting","SOURCE_DEPENDENCE",lambda:independent_sources(["USDA-source-A","USDA-source-A"]))
    neg("N5k360 unknown absolute scale","GEOMETRY_OR_GROUP_HOLD",lambda:verify_geometry(pending("unavailable scale"),True))
    neg("incremental scans treated independent","GEOMETRY_OR_GROUP_HOLD",lambda:verify_geometry(slot_value(1.0),False))
    neg("SNAPMe aggregation before grain qualified","AGGREGATION_NOT_QUALIFIED",lambda:require_aggregation("IMAGE_LINK_ROW",["r1","r2"],["m1","m2"]))
    neg("replicated whole meal contribution even if grain declared","DUPLICATE_AGGREGATION",lambda:require_aggregation("SOURCE_FOOD_RECORD",["r1","r2"],["m1","m1"],True))
    neg("daily record relabeled habitual","DIETARY_STATE_INFLATION",lambda:mutate(d,lambda z:z["payload"].update(observation_window="HABITUAL")))
    neg("system or evaluator view requested outside scope","PROJECTION_NOT_AUTHORIZED",lambda:dev_projection(qa,"SYSTEM_VIEW"))
    neg("hidden gold added to allowlist projection","PROJECTION_CLOSURE",lambda:validate_dev_projection(dict(dev_projection(qa),gold="synthetic-hidden-answer")))
    neg("source hash nested in field list","PROJECTION_CLOSURE",lambda:validate_dev_projection(dict(dev_projection(qa),field_names=["answer",{"hash":"hidden"}])))
    neg("agent-only reference promoted to Gold","REFERENCE_NOT_QUALIFIED",lambda:require_reference("AGENT","QUALIFIED","Q-MASS"))
    neg("mutated immutable revision","REVISION_INTEGRITY",lambda:mutate(m,lambda z:z["payload"].update(component_key="tampered"),reseal=False))
    neg("missing instance_class","ENVELOPE_FIELDS",lambda:mutate(m,lambda z:z.pop("instance_class")))
    neg("mixed instance in real-source only ingest","REAL_ONLY_PROFILE",lambda:mutate(m,lambda z:z.update(instance_class="MIXED_CONSTRUCTED")))
    neg("synthetic source promoted to real","REAL_WITH_SYNTHETIC_SOURCE",lambda:mutate(m,lambda z:z.update(source_class="SYNTHETIC_TEXT")))
    neg("source document referenced as study identity","REF_KIND_MISMATCH",lambda:resolve(idx,ref(art),"StudyIdentity"))
    neg("evidence/claim type conflation cannot pass grounding validator","REF_KIND_MISMATCH",lambda:resolve(idx,ref(nr),"ScientificClaim"))
    neg("same database calculation claimed chemical assay","REFERENCE_PROFILE_MISMATCH",lambda:validate_measurement_use(m["payload"],"CHEMICAL_ASSAY_CLAIM"))
    neg("unknown denominator passed to calculation","MEASUREMENT_NOT_QUALIFIED",lambda:validate_measurement_use(m["payload"]))
    neg("canonical normalized value invented","UNQUALIFIED_NORMALIZATION",lambda:mutate(m,lambda z:z["payload"].update(normalized_value=slot_value("1"))))
    neg("unqualified source basis fabricated","SOURCE_BASIS_HOLD",lambda:mutate(m,lambda z:z["payload"].update(original_basis=slot_value("PER_100G"))))
    neg("public exposed data promoted to locked probe","PROBE_NOT_INDEPENDENT",lambda:require_locked_probe(True,False,True,True))
    neg("development data requested for locked release","RELEASE_BLOCKED",lambda:require_release(qa,"LOCKED_EVALUATION"))
    neg("unqualified development reference requested for training","RELEASE_BLOCKED",lambda:require_release(m,"FUTURE_TRAINING"))
    neg("evidence-backed field changed despite valid revision digest","CANONICAL_SOURCE_DRIFT",lambda:mutate(m,lambda z:z["payload"]["bindings"]["value"].update(raw_value="999999")))
    neg("source anchor raw record hash mismatch","NATIVE_RAW_DIGEST",lambda:mutate(nr,lambda z:z["payload"].update(raw_sha256="0"*64)))
    neg("source record has invalid anchor locator","ANCHOR_MISMATCH",lambda:mutate(nr,lambda z:z["payload"].update(locator={"line":-1})))
    def duplicate_locator():
        z=copy.deepcopy(nr);z["object_id"]+=":duplicate";seal(z)
        validate_set(closure(nr)+[nr,z])
    neg("duplicated native record locator","DUPLICATE_NATIVE_LOCATOR",duplicate_locator)
    def wrong_parent():
        p=next(x for x in bykind["FoodEntityDraft"] if x["payload"]["bindings"].get("code") and str(x["payload"]["bindings"]["business_id"]["raw_value"])!=str(r["payload"]["bindings"]["ingredient_id"]["raw_value"]))
        def change(z):
            old=z["payload"]["parent_ref"]["value"]
            z["payload"]["parent_ref"]=slot_value(ref(p))
            z["dependency_refs"]=[x for x in z["dependency_refs"] if x!=old]+[ref(p)]
        mutate(r,change,(ref(p),))
    neg("wrong NutriData parent ID despite plausible name","BUSINESS_KEY_CODE_MISMATCH",wrong_parent)
    neg("unqualified link promoted to same physical instance","LINK_PROMOTION",lambda:mutate(link,lambda z:z["payload"].update(relation_type="SAME_PHYSICAL_INSTANCE")))
    neg("future release flag or frozen record inserted into draft","DEV_ONLY",lambda:mutate(m,lambda z:z.update(lifecycle="FROZEN")))
    report={"run_id":"B1-U2A-NEGATIVE-001","contract_version":VERSION,"tests":result,"total":len(result),"passed":sum(x["pass"] for x in result),"failed":sum(not x["pass"] for x in result),"scope":"B1 implemented rules and real-object mutations; not full UDF section 35 experiment/temporal/E2H validation","scientific_release_authorized":False}
    atomic_json(out,report)
    print(json.dumps(report,ensure_ascii=False))
    return report["failed"]==0
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run",type=P.Path,required=True);p.add_argument("--out",type=P.Path,required=True);a=p.parse_args()
    raise SystemExit(0 if test(a.run,a.out) else 1)
