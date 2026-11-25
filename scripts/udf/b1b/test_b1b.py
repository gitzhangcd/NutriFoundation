#!/usr/bin/env python3
"""Independent persisted-artifact checks and fail-closed mutation tests; no data values exported."""
import argparse,collections as C,copy,json,pathlib as P,sys
from decimal import Decimal
HERE=P.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"b1"),str(HERE)]
from run_b1b import verify_inputs,authority_records,Ledger,entity_key,build_links,atomic_json,file_sha,INPUT
from contract import ref,resolve,require,ContractError,canon,digest,namespace_of,slot_value,pending
from semantics import *
from bridge import *
from audit_b1b import total_guard,fndds_candidate,gate_flag
def load(p):return json.loads(p.read_text(encoding="utf8"))
def main(root,run):
    root=root.resolve();run=run.resolve()
    objs,idx,resolver=verify_inputs(root);sources=authority_records(root)
    manifest=load(run/"private/collection_manifest.json")
    rows=[];by=C.defaultdict(list)
    for f in sorted((run/"private/typed_collections").glob("*.jsonl")):
        require(f.name in manifest and file_sha(f)==manifest[f.name]["sha256"],"B1B_OUTPUT_HASH")
        with f.open(encoding="utf8") as h:
            x=[json.loads(l) for l in h]
        require(len(x)==manifest[f.name]["rows"] and all(o["kind"]==f.stem for o in x),"B1B_OUTPUT_COLLECTION")
        rows+=x;by[f.stem]+=x
    L=Ledger(idx,rows[0]["created_time"]);ridx=L.validate(rows)
    require(len(rows)==5665 and len(by)==10,"B1B_OUTPUT_COUNT")
    aref={o["payload"]["authority_key"]:o for o in by["AuthoritySnapshot"]}
    require({k:canon(o["payload"]) for k,o in aref.items()}=={k:canon(v) for k,v in sources.items()},"AUTHORITY_REPLAY")
    defs={ref(o):o for o in by["MeasurementDefinition"]}
    ns={o["payload"]["native_namespace"]:o["payload"] for o in by["NativeNamespace"]}
    nsrefs={ref(o):o for o in by["NativeNamespace"]}
    for k,o in defs.items():
        d=o["payload"];validate_definition(d)
        require(len(o["dependency_refs"])==1 and ridx[o["dependency_refs"][0]]["kind"]=="ComponentConcept","DEFINITION_COMPONENT_REVISION")
        require(ridx[o["dependency_refs"][0]]["payload"]["component_id"]==d["component_ref"],"DEFINITION_COMPONENT_REF")
        require(all(ref(aref[a]) in o["provenance_refs"] for a in d["authority_keys"]),"DEFINITION_AUTHORITY_REF")
    mcheck=0;convcheck=0
    for o in by["MeasurementInterpretation"]:
        p=copy.deepcopy(o["payload"]);dref=p["measurement_definition_ref"];d=defs[dref]["payload"]
        x=idx[p["source_measurement_ref"]]
        require(x["kind"]=="NutrientMeasurementDraft","INTERPRETATION_SOURCE_TYPE")
        cr=p.pop("conversion_ref");conv=None
        if cr["tag"]=="VALUE":
            c=ridx[cr["value"]];require(c["kind"]=="RepresentationConversion","CONVERSION_REF_TYPE")
            conv=copy.deepcopy(c["payload"]);require(conv.pop("source_measurement_ref")==ref(x) and conv.pop("measurement_definition_ref")==dref,"CONVERSION_DEPENDENCY")
            require(ref(c) in o["dependency_refs"],"CONVERSION_REF_NOT_DEPENDENCY")
            convcheck+=1
        p["measurement_definition_ref"]=d["measurement_definition_id"];p["conversion"]=conv
        validate_interpretation(x,idx,d,p);mcheck+=1
    require(mcheck==2851 and convcheck==520,"MEASUREMENT_REPLAY_COUNTS")
    for o in by["NamespaceBinding"]:
        p=o["payload"];x=idx[p["native_ref"]];a=idx[p["artifact_ref"]]
        nsx=nsrefs[p["namespace_ref"]]["payload"]
        require(x["kind"]=="NativeRecord" and a["kind"]=="SourceArtifact" and p["artifact_ref"]==x["payload"]["artifact_ref"] and canon(p["key_value"])==canon(x["payload"]["locator"]),"NAMESPACE_BINDING_REPLAY")
        require(a["payload"]["namespace"]==nsx["native_namespace"] and p["artifact_ref"] in nsx["snapshot_artifact_refs"] and p["global_entity"] is False,"NAMESPACE_ARTIFACT_BINDING")
    keypairs=C.defaultdict(list)
    for o in by["NamespaceKeyBinding"]:
        p=o["payload"];x=idx[p["source_object_ref"]];dom,field,val=entity_key(x);n=namespace_of(idx,x)
        require(p["namespace_id"]==ns[n]["namespace_id"] and p["key_domain"]==dom and p["key_field"]==field and canon(p["key_value"])==canon(val),"NAMESPACE_KEY_REPLAY")
        keypairs[(dom,canon(val))].append(p)
    links,_=build_links(objs,idx,ns)
    require({p["source_candidate_ref"]:canon(p) for p in links}=={o["payload"]["source_candidate_ref"]:canon(o["payload"]) for o in by["NamespaceLinkQualification"]},"LINK_REPLAY")
    qcheck=0
    for o in by["QuantityInterpretation"]:
        p=o["payload"];x=idx[p["source_object_ref"]];b=x["payload"]["bindings"]
        require(p["measurement_definition_ref"] in defs,"QUANTITY_DEFINITION_REF")
        if x["kind"]=="RecipeIngredientDraft":
            require(canon(qline(b["amount"]["raw_value"],p["unit"],p["basis"]))==canon(p["missingness"]),"NOTE_REPLAY")
        else:
            require(x["kind"]=="DietaryObservationDraft" and canon(p["source_raw"])==canon(b["FoodAmt"]["raw_value"]) and canon(p["duplicate_raw_column_retained"])==canon(b["FoodAmt.1"]["raw_value"]) and p["aggregation"]=="NO_AGGREGATION_ONE_FIELD_NOT_TWO","FOODAMT_REPLAY")
        qcheck+=1
    legacy=load(run/"private/D0SharedProjection.json");side=load(run/"private/D0SharedBridgeSidecar.json")
    back=reverse(legacy,side);expected={ref(o):o for o in objs if o["kind"] in KINDS}
    require({ref(x):canon(x) for x in back}=={r:canon(x) for r,x in expected.items()},"D0_BRIDGE_DISK_REPLAY")
    audit=load(run/"SourceConsistencyAudit.json")
    require(audit["nutrition5k"]["dish_rows_any_total_conflict"]==681 and audit["snapme"]["code_invalid_lexical_rows"]==121,"SOURCE_CONFLICT_AUDIT")
    # Actual examples for mutation tests, and synthetic boundary inputs where indicated.
    real_m=next(o for o in objs if o["kind"]=="NutrientMeasurementDraft" and str(o["payload"]["bindings"]["value"]["raw_value"]).strip().lower()=="tr")
    d=definition(real_m["payload"]["component_key"]);mi=interpret_measurement(real_m,idx,d)
    a,b=next((u,v) for arr in keypairs.values() for u in arr for v in arr if u["namespace_id"]!=v["namespace_id"])
    tests=[]
    def pos(name,fn):
        try:fn();tests.append({"name":name,"expected":"ACCEPT","observed":"ACCEPT","pass":True})
        except Exception as e:tests.append({"name":name,"expected":"ACCEPT","observed":type(e).__name__+":"+str(e)[:90],"pass":False})
    def neg(name,code,fn):
        try:fn();tests.append({"name":name,"expected":code,"observed":"ACCEPT","pass":False})
        except ContractError as e:tests.append({"name":name,"expected":code,"observed":str(e),"pass":str(e)==code})
        except Exception as e:tests.append({"name":name,"expected":code,"observed":type(e).__name__+":"+str(e)[:90],"pass":False})
    pos("real measurement definition revalidated",lambda:validate_definition(d))
    pos("all persisted measurement/quantity/namespace bindings replayed",lambda:require(mcheck==2851 and convcheck==520 and qcheck==266 and len(by["NamespaceBinding"])==747 and len(links)==578,"REPLAY"))
    pos("decimal numerator conversion",lambda:require(mass_unit_transform("1000","mg","g")==Decimal("1"),"CONVERSION"))
    pos("known reported zero is a value, not measured zero",lambda:require(missingness("0")["lexical_class"]=="REPORTED_NUMERIC_ZERO" and not missingness("0")["measured_zero_proved"],"ZERO"))
    pos("declared source key relation",lambda:qualify_namespace(ns,"nutridata:dish","nutridata:ingredient","BUSINESS_ID_AND_CODE"))
    pos("same source key structural equality",lambda:require(identity_guard(a,a,"SOURCE_KEY_EQUALITY"),"KEY"))
    pos("actual shared D0 artifacts and anchors exact reverse",lambda:require(len(back)==770,"BRIDGE"))
    pos("8-digit lexical FoodCode candidate only",lambda:require(fndds_candidate("12345678","FNDDS_2015_16_DECLARED_BY_ASA24_2020")["external_join"].startswith("HOLD"),"CODE"))
    pos("OFF synthetic mg input converted to standard g",lambda:require(off_row_check({"nutrition_data_per":"100g","nutriments":{"sodium_100g":"0.5","sodium_value":"500","sodium_unit":"mg"}},"sodium")["status"]=="ROW_NUMERATOR_CONSISTENT","OFF"))
    neg("actual Tr replaced with numeric zero","MISSINGNESS_PROMOTION",lambda:missingness_guard(mi["source_raw"],missingness("0")))
    def mutate_definition(**kw):x=copy.deepcopy(d);x.update(kw);return validate_definition(x)
    neg("unknown NutriData basis invented","DEFINITION_POLICY_DRIFT",lambda:mutate_definition(basis=slot_value("PER_100G")))
    neg("measurement unit changed despite valid source key","DEFINITION_POLICY_DRIFT",lambda:mutate_definition(unit=slot_value("kg")))
    neg("source field definition promoted to scientific measurement","SCIENCE_QUALIFICATION_INFLATION",lambda:mutate_definition(qualification="SCIENCE_CALCULATION_QUALIFIED"))
    neg("source semantics used as qualified calculation","MEASUREMENT_CALCULATION_HOLD",lambda:qualified_calculation(d,mi))
    def mutate_i():
        x=copy.deepcopy(mi);x["missingness"]=missingness("0");return validate_interpretation(real_m,idx,d,x)
    neg("real persisted interpretation altered","INTERPRETATION_DRIFT",mutate_i)
    for x,y,label in [("CARBOHYDRATE_AVAILABLE","CARBOHYDRATE_UNSPECIFIED","available vs unspecified carbohydrate"),("CARBOHYDRATE_AVAILABLE","CARBOHYDRATE_TOTAL","available vs total carbohydrate"),("VITAMIN_A_RAE","VITAMIN_A_RE","RAE vs RE"),("FOLATE_TOTAL","FOLATE_DFE","folate vs DFE"),("FOLIC_ACID","FOLATE_FOOD","folic acid vs food folate"),("SODIUM","SALT","sodium vs salt"),("GI","CARBOHYDRATE_AVAILABLE","GI vs carbohydrate"),("NRV_PERCENT","ENERGY","NRV ratio vs energy")]:
        neg(label,"COMPONENT_DEFINITION_MISMATCH",lambda x=x,y=y:exact_component_mapping(x,y))
    neg("100 mL to 100 g without density","DENSITY_REQUIRED",lambda:conversion_guard("PER_100ML","PER_100G","RAW","RAW"))
    neg("serving to 100g without portion mass","SERVING_MASS_REQUIRED",lambda:conversion_guard("PER_SERVING","PER_100G","RAW","RAW"))
    neg("raw to cooked not unit conversion","STATE_OR_PREPARATION_UNQUALIFIED",lambda:conversion_guard("PER_100G","PER_100G","RAW","COOKED"))
    neg("unknown preparation passed to comparison","STATE_OR_PREPARATION_UNQUALIFIED",lambda:conversion_guard("PER_100G","PER_100G","UNKNOWN","UNKNOWN"))
    neg("incompatible numerator unit","INCOMPATIBLE_NUMERATOR_UNIT",lambda:mass_unit_transform("1","kcal","g"))
    neg("actual equal raw key in two namespaces","CROSS_NAMESPACE_IDENTITY",lambda:identity_guard(a,b,"SOURCE_KEY_EQUALITY"))
    neg("same namespace category treated as physical item","INSTANCE_EQUIVALENCE_NOT_AUTHORIZED",lambda:identity_guard(a,a,"SAME_PHYSICAL_INSTANCE"))
    neg("N5k parent edge pointed to unrelated NutriData namespace","CROSS_NAMESPACE_RELATION_UNQUALIFIED",lambda:qualify_namespace(ns,"fallback:Nutrition5k:dish","nutridata:ingredient","PADDED_INGREDIENT_ID"))
    neg("wrong EPIC key type","CROSS_NAMESPACE_RELATION_UNQUALIFIED",lambda:qualify_namespace(ns,"epic100:train","epic100:noun_class","EPIC_VERB_KEY"))
    neg("5-digit code padded or accepted as FNDDS","FNDDS_CODE_LEXICAL",lambda:fndds_candidate("12345","FNDDS_2015_16_DECLARED_BY_ASA24_2020"))
    neg("cross-cycle FNDDS code join","FNDDS_VERSION_MISMATCH",lambda:fndds_candidate("12345678","FNDDS_2021_23"))
    neg("unknown recipe note converted into grams","RECIPE_NOTE_UNIT_BASIS_HOLD",lambda:qline("5",slot_value("g"),pending("unknown")))
    neg("conflicted total used as reference candidate","SOURCE_TOTAL_CONFLICT",lambda:total_guard(gate_flag(Decimal("0.1"))))
    neg("unknown total flag treated as reference","SOURCE_TOTAL_FLAG_UNRESOLVED",lambda:total_guard("UNKNOWN"))
    # Reseal the D0 transport object, so the bridge must detect semantic/reverse errors.
    aa=next(i for i,o in enumerate(legacy) if o["kind"]=="SourceAnchor")
    art=next(i for i,o in enumerate(legacy) if o["kind"]=="SourceArtifact")
    def patch_bridge(i,fn):
        x=copy.deepcopy(legacy);fn(x[i]);x[i]["revision_id"]=legacy_revision(x[i]);return reverse(x,side)
    neg("bridge promoted to SYSTEM purpose","D0_BRIDGE_PURPOSE_OR_LIFECYCLE",lambda:patch_bridge(aa,lambda z:z.update(purpose_release_ref="LOCKED_EVALUATION")))
    neg("bridge source_class changed","D0_BRIDGE_SOURCE_INSTANCE",lambda:patch_bridge(aa,lambda z:z.update(source_class="REAL_DOCUMENT")))
    neg("bridge instance_class removed","D0_BRIDGE_FIELDS",lambda:patch_bridge(aa,lambda z:z.pop("instance_class")))
    neg("bridge source hash tampered","D0_BRIDGE_SOURCE_HASH",lambda:patch_bridge(aa,lambda z:z.update(source_version="0"*64)))
    neg("anchor referenced as artifact","D0_BRIDGE_TYPED_SOURCE",lambda:patch_bridge(aa,lambda z:z.update(source_ref=z["object_id"])))
    neg("hidden content inserted","D0_BRIDGE_CONTENT_OR_SOURCE",lambda:patch_bridge(aa,lambda z:z.update(content_or_content_ref=slot_value("forbidden content"))))
    neg("bridge source made qualified reference","D0_BRIDGE_ARTIFACT_PROMOTION",lambda:patch_bridge(art,lambda z:z.update(qualification_status="QUALIFIED")))
    neg("duplicate sidecar entry","D0_BRIDGE_ONE_TO_ONE",lambda:reverse(legacy,side+[side[0]]))
    def side_inflation():
        x=copy.deepcopy(side);x[0]["b1_purpose_release_ref"]=slot_value("unapproved-release");return reverse(legacy,x)
    neg("sidecar synthetic release ref","D0_BRIDGE_SOURCE_RELEASE_OR_SUPERSESSION",side_inflation)
    def alter_locator():return patch_bridge(aa,lambda z:z.update(locator={"line":999999}))
    neg("resealed locator differs from immutable B1 revision","REVISION_INTEGRITY",alter_locator)
    neg("bridge artifact type StudyIdentity","D0_BRIDGE_KIND_UNAUTHORIZED",lambda:patch_bridge(art,lambda z:z.update(kind="StudyIdentity")))
    pos("missing legacy instance class stays unresolved",lambda:require(migration_status({"kind":"StudyIdentity"})=="HOLD_LEGACY_INSTANCE_CLASS_UNRESOLVED","MIGRATION"))
    report={"run_id":"B1-U2B-VALIDATION-002","persisted_semantics_replayed":mcheck,"representation_conversions_replayed":convcheck,
            "quantity_interpretations_replayed":qcheck,"namespace_bindings_replayed":len(by["NamespaceBinding"]),"source_key_bindings_replayed":len(by["NamespaceKeyBinding"]),
            "namespace_links_replayed":len(links),"bridge_persisted_exact_reverse":len(back),"new_typed_objects_validated":len(rows),
            "tests":tests,"total":len(tests),"positive":sum(t["expected"]=="ACCEPT" for t in tests),"negative":sum(t["expected"]!="ACCEPT" for t in tests),
            "passed":sum(t["pass"] for t in tests),"failed":sum(not t["pass"] for t in tests),"qualification":"DEVELOPMENT_ONLY"}
    atomic_json(run/"ContractValidationReport.json",report)
    print(json.dumps({k:v for k,v in report.items() if k!="tests"},ensure_ascii=False))
    for t in tests:
        if not t["pass"]:print("FAIL",t)
    require(report["failed"]==0,"U2B_CONTRACT_TEST_FAILURE")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--run",type=P.Path,required=True);a=p.parse_args();main(a.root,a.run)
