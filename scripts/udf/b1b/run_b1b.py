#!/usr/bin/env python3
"""B1/U2-B: bounded semantics and shared-identity bridge on pinned real_003.
Run from NutriOne root. Does not alter source files, U2-A records, D0 or releases.
"""
import argparse, collections as C, copy, hashlib, json, pathlib as P, sys, zipfile
from datetime import datetime, timezone
from decimal import Decimal
HERE=P.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"b1"),str(HERE)]
from run_b1 import read_back,atomic_json,file_sha
from contract import validate_set,ref,resolve,namespace_of,require,ContractError,canon,digest,slot_value,pending,na,validate_slot
from semantics import *
from bridge import forward,reverse,run_d0,verify_snapshot,PIN,BRIDGE_VERSION

BASE=P.Path("runs/B1/U2-A/real_003")
INPUT=P.Path("runs/B1/U2-B/inputs")
FENCES={
 "RealSampleRoundTripReport.json":"f8a4e6dbcb58746a649701f3ac13c7740a94e6e0d36a1f4748441ed8222d27e1",
 "private/source_resolver.json":"1365ca2b1d719ad450d6e11c2f5c10e8ec90dd9cac470aaab81abf6c338f3b7e",
 "private/collection_manifest.json":"0d5fde43d7629810bec085c659fedfe77846dcd774e160e82f2b491d2c154507"}
LOCAL_AUTH={
 "ND_PUBLIC":(INPUT/"NutriData_Public.html","2899d21ecb1700116351b9847bcc88b90ca06bf41cfba2894220dd6c7a66f6ca","public ingredient and dish library descriptions; not a field dictionary"),
 "OFF_SCHEMA":(INPUT/"OFF_ProductNutrition.html","d5f62e897990d8ba76671aa7de2281f48757b108fbd513f90be2c6f07ef456b0","nutriments patternProperties: _100g, _value, _unit; carbohydrates and carbohydrates-total"),
 "OFF_CONFLICT":(INPUT/"OFF_ExplainNutrition.html","7e9112acb5ea8c877b6eab1db692834aa5c2a198ee577f2b6f85ee456004347a","developer explanation of _100g conflicts with detailed schema"),
 "SN_PAPER":(INPUT/"SNAPMe_Study.html","7eeb15a90ffb5f3a27f059833e188a34c30fbfae830760a0da7cee6cc7ff7867","study methods, ASA24 version 2020 and photo-to-item linkage"),
 "ASA_VERSION":(INPUT/"ASA24_2020_Version.html","584e97a6a8b272d0c2ba3207ece35a2cab2e1bcee454384b5943574acac40b93","ASA24-2020 version documentation; FNDDS and FPED 2015-16"),
 "ASA_ITEMS":(INPUT/"ASA24_2020.zip","86f1492650d409427223615616d9dcd47ab1013258fad987ff7b08cf293201e5","2020Record/DataDictionary_ITEMS_2020Record.xls; DATADICTIONARY field rows"),
 "N5_README":(P.Path("source_data/public_samples/20261125_run001/NDF-G013/nutrition5k_README.md"),"4c77ceab6dfcaf7b23019fae6c323f237f93ecd4213ebe44b36b8f8583c84ae0","Ingredient Metadata; Dish Metadata; Train/Test Splits; actual 6+7n row layout established in B0"),
 "MENU_README":(P.Path("source_data/public_samples/20261125_run001/NDF-G017/zip_01_readme.txt"),"9a8d02f9f642197084e67d124d324fb9e62c1c17bc9cc27b8e1c43e982f0b046","source items_info and labels file description"),
 "UDF":(P.Path("docs/AI_Nutri_Unified_Data_Foundation_v2.1.md"),"3c0ef69f9ecff2178830c0b4d43253dae5c161d7308c86bc2b6be5e6a68b26ed","sections 11,15-22,34-37,41")}
NDSF_SHA="81426a9423f825681a155b748643ebd9f3b6d992b67304d35e94abd9f9ca90ce"
D0_SPEC_SHA="bade6cdad0199e29bbf29471d078d32e5fcb8bc6b03a5d9f800d986c7103ada7"
ASA_MEMBER="2020Record/DataDictionary_ITEMS_2020Record.xls"
ASA_MEMBER_SHA="cda58233f16258132dd10744ed472b820632bdd63e99b3ff79e83da6c1ce3758"
ASA_EXPECTED_ROWS={"FOODAMT":27,"KCAL":28,"PROT":29,"TFAT":30,"CARB":31,"FIBE":37,"SODI":43,"FOLA":52,"FA":53,"FF":54,"FDFE":55,"VARA":57}
ASA_UNIT_HINTS={"g":"(g)","mg":"(mg)","kcal":"(kcal)","ug":"(mcg)","ug_RAE":"(mcg_rae)","ug_DFE":"(mcg_dfe)"}
def jload(p):return json.loads(p.read_text(encoding="utf8"))
def blob(p):
    b=p.read_bytes();return hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
def verify_inputs(root):
    for p,h in FENCES.items():require(file_sha(root/BASE/p)==h,"U2A_FENCE_CHANGED")
    require(blob(root/BASE/"RealSampleRoundTripReport.json")=="efa155d1ae6d3b79fe9e707620110d4a316dbc86","U2A_REPORT_BLOB")
    m=jload(root/BASE/"private/collection_manifest.json")
    tbl=root/BASE/"private/typed_collections"
    require(set(m)=={p.name for p in tbl.glob("*.jsonl")} and len(m)==17,"U2A_COLLECTION_SET")
    for name,v in m.items():
        p=tbl/name;require(p.stat().st_size==v["bytes"] and file_sha(p)==v["sha256"],"U2A_COLLECTION_HASH")
        with p.open(encoding="utf8") as h:require(sum(1 for _ in h)==v["rows"],"U2A_COLLECTION_ROWS")
    resolver=jload(root/BASE/"private/source_resolver.json")
    objs=read_back(tbl);idx=validate_set(objs)
    require(len(objs)==5699 and len(resolver)==23,"U2A_COUNTS")
    srcs={ref(o):o for o in objs if o["kind"]=="SourceArtifact"}
    require(set(srcs)==set(resolver),"U2A_ARTIFACT_FENCE")
    for k,v in resolver.items():
        p=root/v["path"];require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root/"source_data"),"U2A_SOURCE_PATH")
        require(file_sha(p)==v["sha256"]==srcs[k]["payload"]["file_sha256"] and v["namespace"]==srcs[k]["payload"]["namespace"],"U2A_SOURCE_HASH")
    return objs,idx,resolver
def authority_records(root):
    d={}
    for k,(p,h,locator) in LOCAL_AUTH.items():
        q=root/p;require(q.is_file() and file_sha(q)==h,"AUTHORITY_HASH")
        d[k]={"authority_key":k,"source":AUTH[k],"sha256":h,"locator":locator,"bytes":q.stat().st_size,"verification":"LOCAL_SOURCE_BYTES_VERIFIED"}
    # Project norm is inspected cloud-side, not automatically copied into Mac or a real empirical source.
    d["NDSF"]={"authority_key":"NDSF","source":AUTH["NDSF"],"sha256":NDSF_SHA,"locator":"Part III.2.2-III.3.2: envelope, Slot, axes, measurement definition","verification":"PROJECT_UPSTREAM_DOCUMENT_HASH_RECORDED_CLOUD"}
    d["NDF_D0_SPEC"]={"authority_key":"NDF_D0_SPEC","source":"NDF-D0-D2 + NDS-R1 integrated execution protocol","sha256":D0_SPEC_SHA,"locator":"D0 §§5-10","verification":"PROJECT_UPSTREAM_DOCUMENT_HASH_RECORDED_CLOUD"}
    # Binary XLS reader was installed within run inputs, not into system python.
    sys.path.insert(0,str(root/INPUT/"xlrd_vendor"))
    import xlrd
    require(xlrd.__version__=="2.0.2","XLRD_VERSION")
    with zipfile.ZipFile(root/INPUT/"ASA24_2020.zip") as z:
        raw=z.read(ASA_MEMBER)
    require(hashlib.sha256(raw).hexdigest()==ASA_MEMBER_SHA,"ASA24_ITEMS_MEMBER_HASH")
    sh=xlrd.open_workbook(file_contents=raw).sheet_by_name("DATADICTIONARY")
    extracted=[]
    for k,row in ASA_EXPECTED_ROWS.items():
        v=sh.row_values(row-1);require(str(v[0]).strip().upper()==k,"ASA24_FIELD_LOCATOR")
        desc=str(v[1]).strip();unit=ASA[k][1]
        require(ASA_UNIT_HINTS[unit] in desc.lower() if k!="FOODAMT" else "grams" in desc.lower(),"ASA24_FIELD_UNIT")
        extracted.append({"field":k,"row":row,"description":desc,"data_type":str(v[2]).strip(),"unit_interpretation":unit})
    d["ASA_ITEMS"]["zip_member"]=ASA_MEMBER;d["ASA_ITEMS"]["member_sha256"]=ASA_MEMBER_SHA
    d["ASA_ITEMS"]["worksheet"]="DATADICTIONARY";d["ASA_ITEMS"]["verified_field_rows"]=extracted
    d["ASA_ITEMS"]["reader"]="xlrd==2.0.2 local dependency"
    return d
def entity_key(o):
    p=o["payload"];b=p.get("bindings",{});k=o["kind"]
    if k=="FoodEntityDraft":field="business_id";dom="SOURCE_FOOD_ENTITY_KEY"
    elif k=="FoodInstanceDraft":field="dish_id";dom="SOURCE_SCAN_KEY"
    elif k=="FoodLabelDraft":field="business_id" if "business_id" in b else "label";dom="SOURCE_CATEGORY_LABEL_NOT_INSTANCE"
    elif k=="RecipeDraft" and "business_id" in b:field="business_id";dom="SOURCE_RECIPE_KEY"
    elif k=="ProductVersionDraft":field="code";dom="SOURCE_BARCODE_SNAPSHOT"
    elif k=="QARecordDraft":field="qid";dom="SOURCE_QA_KEY"
    elif k=="ProcessObservationDraft":field="narration_id";dom="SOURCE_ACTION_KEY"
    elif k=="ProcessVocabularyDraft":field="business_id";dom="SOURCE_PROCESS_VOCABULARY_KEY"
    elif k=="VideoMetadataDraft":field="business_id";dom="SOURCE_VIDEO_METADATA_KEY"
    else:return None
    if field not in b:return None
    return dom,field,copy.deepcopy(b[field]["raw_value"])
def build_links(objs,idx,ns):
    links=[];counts=C.Counter()
    for o in objs:
        p=o["payload"];kind=o["kind"]
        if kind=="RecipeIngredientDraft":
            if p["parent_ref"]["tag"]!="VALUE":
                counts["nutridata_unmatched_hold"]+=1;continue
            l=namespace_of(idx,o);r=namespace_of(idx,resolve(idx,p["parent_ref"]["value"],"FoodEntityDraft"))
            rule="BUSINESS_ID_AND_CODE"
        elif kind=="NativeLinkDraft":
            lobj=idx[p["left_ref"]];robj=idx[p["right_ref"]];l=namespace_of(idx,lobj);r=namespace_of(idx,robj)
            if l.startswith(N5):rule="PADDED_INGREDIENT_ID"
            elif l=="menumatch:labels":rule="MENU_LABEL_KEY"
            else:rule={"epic100:verb_class":"EPIC_VERB_KEY","epic100:noun_class":"EPIC_NOUN_KEY","epic100:video_id":"EPIC_VIDEO_KEY"}.get(r)
        else:continue
        result=qualify_namespace(ns,l,r,rule);counts[rule]+=1
        links.append({"source_candidate_ref":ref(o),"left_namespace":l,"right_namespace":r,"rule":rule,"qualification":result,"same_physical_instance":False})
    return links,counts
class Ledger:
    def __init__(self,base,when):
        self.base=base;self.when=when;self.index={};self.kinds=C.defaultdict(list)
    def emit(self,k,key,p,provenance=(),dependencies=(),origin="CON",real=False,source_class="REAL_DATA"):
        o={"object_id":"b1b:"+k+":"+digest([VERSION,key])[:40],"kind":k,"schema_version":VERSION,"contract_version":VERSION,
           "lifecycle":"DRAFT","producer_role":"B1B_SEMANTIC_ADAPTER","created_time":self.when,"clock_axis":"AUDIT_UTC",
           "source_class":source_class,"instance_class":"REAL_SOURCE_GROUNDED" if real else "MIXED_CONSTRUCTED",
           "construction_class":origin,"provenance_refs":list(dict.fromkeys(provenance)),"dependency_refs":list(dict.fromkeys(dependencies)),
           "purpose":"CURATION_DEV","purpose_release_ref":pending("no release authorized"),"supersedes_ref":na("first U2-B draft revision"),"payload":copy.deepcopy(p)}
        o["revision_id"]=digest(o);r=ref(o);require(r not in self.index,"B1B_DUPLICATE_OBJECT")
        self.index[r]=o;self.kinds[k].append(o);return r
    def validate(self,objects=None):
        objects=objects if objects is not None else list(self.index.values())
        refs={ref(o):o for o in objects};require(len(refs)==len(objects),"B1B_DUPLICATE_OBJECT")
        for r,o in refs.items():
            t=dict(o);h=t.pop("revision_id")
            require(digest(t)==h,"B1B_REVISION_DIGEST")
            require(o["lifecycle"]=="DRAFT" and o["purpose"]=="CURATION_DEV" and o["purpose_release_ref"]["tag"]=="PENDING","B1B_RELEASE_HOLD")
            require(o["instance_class"] in ("REAL_SOURCE_GROUNDED","MIXED_CONSTRUCTED") and o["construction_class"] in ("OBS","CON","DRV"),"B1B_AXES")
            require(bool(o["provenance_refs"]) or o["kind"]=="AuthoritySnapshot","B1B_PROVENANCE")
            for x in o["provenance_refs"]+o["dependency_refs"]:
                require(x in self.base or x in refs,"B1B_ORPHAN")
                require(x!=r,"B1B_SELF_REF")
                if o["instance_class"]=="REAL_SOURCE_GROUNDED" and x in refs:require(refs[x]["instance_class"]=="REAL_SOURCE_GROUNDED","B1B_REAL_CONSTRUCTION_INFLATION")
        return refs
def main(root,out):
    root=root.resolve();out=out.resolve();require(not out.exists() and not out.is_relative_to(root/"source_data"),"OUTPUT_OVERWRITE_OR_SOURCE")
    objs,idx,resolver=verify_inputs(root);sources=authority_records(root)
    when=datetime.now(timezone.utc).isoformat();L=Ledger(idx,when)
    a_refs={}
    for k,v in sources.items():
        # NDSF/D0 hash are inspected cloud authority, not represented as local recovered original bytes.
        a_refs[k]=L.emit("AuthoritySnapshot",k,v,origin="OBS",real=True,source_class="REAL_DOCUMENT")
    cs={}
    for k,(family,definition_text) in CONCEPTS.items():
        cs[k]=L.emit("ComponentConcept",k,{"component_id":concept_id(k),"kind_family":family,"definition":definition_text,
            "identity_scope":"LOCAL_DECLARED_ATTRIBUTE_FAMILY","external_mapping":pending("no external exact concept mapping"),
            "qualification":"CANDIDATE_NOT_EQUIVALENCE"},(a_refs["UDF"],a_refs["NDSF"]))
    ms=[o for o in objs if o["kind"]=="NutrientMeasurementDraft"]
    ds={o["payload"]["component_key"]:definition(o["payload"]["component_key"],o["payload"]["original_unit"].get("value")) for o in ms}
    for k in ASA:ds.setdefault(SN+":"+k,definition(SN+":"+k))
    ds["nutridata:dish:major.note"]=definition("nutridata:dish:major.note")
    drefs={}
    for k,d in sorted(ds.items()):
        validate_definition(d);c=d["component_ref"][3:]
        drefs[k]=L.emit("MeasurementDefinition",k,d,tuple(a_refs[x] for x in d["authority_keys"])+(a_refs["NDSF"],), (cs[c],))
    art=C.defaultdict(list)
    for o in objs:
        if o["kind"]=="SourceArtifact":art[o["payload"]["namespace"]].append(o)
    ns={k:ns_record(k,v) for k,v in art.items()}
    nrefs={k:L.emit("NativeNamespace",k,v,tuple(v["snapshot_artifact_refs"]),origin="DRV") for k,v in sorted(ns.items())}
    native_bindings={};keys=[];key_counts=C.Counter();raw_to_namespaces=C.defaultdict(set)
    for o in objs:
        if o["kind"]!="NativeRecord":continue
        p=o["payload"];a=resolve(idx,p["artifact_ref"],"SourceArtifact");n=a["payload"]["namespace"]
        require(p["artifact_ref"] in ns[n]["snapshot_artifact_refs"],"NAMESPACE_ARTIFACT_REF")
        native_bindings[ref(o)]=L.emit("NamespaceBinding",ref(o),{"native_ref":ref(o),"namespace_ref":nrefs[n],"key_domain":"NATIVE_RECORD_LOCATOR",
            "artifact_ref":p["artifact_ref"],"key_value":p["locator"],"identity_scope":"SOURCE_RECORD_ONLY","global_entity":False},(p["anchor_ref"],),(ref(o),nrefs[n]),"DRV")
    for o in objs:
        q=entity_key(o)
        if q is None:continue
        dom,field,val=q;n=namespace_of(idx,o);p=o["payload"];raw_to_namespaces[(dom,canon(val))].add(n)
        key_counts[(n,dom,canon(val))]+=1
        keys.append(L.emit("NamespaceKeyBinding",ref(o),{"source_object_ref":ref(o),"namespace_ref":nrefs[n],"namespace_id":ns[n]["namespace_id"],
            "key_domain":dom,"key_field":field,"key_value":val,"identity_scope":"SOURCE_SCOPED_KEY_NOT_PHYSICAL_IDENTITY",
            "qualification":"STRUCTURE_IDENTIFIED_NOT_CROSS_SOURCE_IDENTITY"},tuple(o["provenance_refs"]),(ref(o),native_bindings[p["native_ref"]],nrefs[n]),"DRV"))
    links,link_counts=build_links(objs,idx,ns)
    for p in links:
        o=idx[p["source_candidate_ref"]]
        L.emit("NamespaceLinkQualification",ref(o),p,tuple(o["provenance_refs"]),(ref(o),nrefs[p["left_namespace"]],nrefs[p["right_namespace"]]),"DRV")
    stats=C.Counter();miss=C.Counter();defs_used=C.Counter();conversions=C.Counter();off=C.Counter();off_discriminating=0
    for o in ms:
        p=o["payload"];key=p["component_key"];d=ds[key];v=interpret_measurement(o,idx,d);validate_interpretation(o,idx,d,v)
        stats[v["field_semantics_status"]]+=1;miss[v["missingness"]["lexical_class"]]+=1;defs_used[key]+=1
        if v["off_row_check"]:
            off[v["off_row_check"]["status"]]+=1
            off_discriminating+=v["off_row_check"]["original_display_unit"]!=d["unit"]["value"]
        conv=v.pop("conversion")
        cr=None
        if conv is not None:
            conversions[conv["operation"]]+=1
            cr=L.emit("RepresentationConversion",ref(o),dict(conv,source_measurement_ref=ref(o),measurement_definition_ref=drefs[key]),
                      tuple(o["provenance_refs"]),(ref(o),drefs[key]),"DRV")
        v["measurement_definition_ref"]=drefs[key];v["conversion_ref"]=slot_value(cr) if cr else na("no representation conversion")
        L.emit("MeasurementInterpretation",ref(o),v,tuple(o["provenance_refs"]),(ref(o),drefs[key])+((cr,) if cr else ()),"DRV")
    recipe_count=0;snap_count=0;snap_equal=0
    for o in objs:
        p=o["payload"]
        if o["kind"]=="RecipeIngredientDraft":
            raw=p["bindings"]["amount"]["raw_value"];mi=qline(raw,p["unit"],p["basis"]);recipe_count+=1;defs_used["nutridata:dish:major.note"]+=1
            dref=drefs["nutridata:dish:major.note"]
            L.emit("QuantityInterpretation",ref(o),{"source_object_ref":ref(o),"measurement_definition_ref":dref,
              "source_raw":raw,"missingness":mi,"unit":p["unit"],"basis":p["basis"],"qualification":"HOLD_RECIPE_AMOUNT_UNIT_BASIS",
              "aggregation":"NO_AGGREGATION"},tuple(o["provenance_refs"]),(ref(o),dref),"DRV")
        elif o["kind"]=="DietaryObservationDraft":
            b=p["bindings"];raw=b["FoodAmt"]["raw_value"];raw2=b["FoodAmt.1"]["raw_value"]
            equal=canon(raw)==canon(raw2);snap_equal+=equal;snap_count+=1;defs_used[SN+":FOODAMT"]+=1
            dref=drefs[SN+":FOODAMT"]
            L.emit("QuantityInterpretation",ref(o),{"source_object_ref":ref(o),"measurement_definition_ref":dref,
             "source_raw":raw,"duplicate_raw_column_retained":raw2,"duplicate_raw_equal":equal,
             "missingness":missingness(raw),"unit":slot_value("g"),"basis":slot_value("SOURCE_REPORTED_ITEM_LINK_ROW"),
             "qualification":"HOLD_INTAKE_EVENT_KEY_AND_MEASUREMENT","aggregation":"NO_AGGREGATION_ONE_FIELD_NOT_TWO"},tuple(o["provenance_refs"]),(ref(o),dref),"DRV")
    # Source and bridge copies remain only local.
    legacy,side=forward(objs);back=reverse(legacy,side)
    expected={ref(o):o for o in objs if o["kind"] in ("SourceArtifact","SourceAnchor")}
    require(set(expected)=={ref(o) for o in back} and all(canon(expected[ref(o)])==canon(o) for o in back),"D0_BRIDGE_EXACT_ROUNDTRIP")
    d0=run_d0(root/INPUT/"d0_snapshot",legacy)
    require(len(legacy)==770 and len(side)==770,"D0_BRIDGE_COUNT")
    L.validate()
    out.mkdir(parents=True);private=out/"private";private.mkdir();tables=private/"typed_collections";tables.mkdir()
    for k,rows in sorted(L.kinds.items()):
        with (tables/(k+".jsonl")).open("x",encoding="utf8") as f:
            for o in rows:f.write(canon(o)+"\n")
    # Preserve exact separate physical collections, and sidecar separately.
    atomic_json(private/"D0SharedProjection.json",legacy);atomic_json(private/"D0SharedBridgeSidecar.json",side)
    loaded=[]
    for f in sorted(tables.glob("*.jsonl")):
        with f.open(encoding="utf8") as h:
            for line in h:
                o=json.loads(line);require(o["kind"]==f.stem,"B1B_TYPED_COLLECTION");loaded.append(o)
    x=L.validate(loaded);require(set(x)==set(L.index) and all(canon(x[r])==canon(L.index[r]) for r in x),"B1B_SERIALIZATION_ROUNDTRIP")
    for key,v in resolver.items():require(file_sha(root/v["path"])==v["sha256"],"U2A_SOURCE_CHANGED_AFTER")
    verify_inputs(root);verify_snapshot(root/INPUT/"d0_snapshot")
    bridge_report={"bridge_version":BRIDGE_VERSION,"projection_objects":len(legacy),"source_artifact_count":sum(o["kind"]=="SourceArtifact" for o in legacy),
                   "source_anchor_count":sum(o["kind"]=="SourceAnchor" for o in legacy),"reverse_exact":len(back),"sidecar_count":len(side),
                   "scope":"SourceArtifact/SourceAnchor only; CURATION_DEV read-only, not SYSTEM_VIEW",
                   "production_interchange":False,"delegated_scientific_kinds":9,**d0}
    atomic_json(out/"D0SharedBridgeReport.json",bridge_report)
    atomic_json(out/"AuthorityEvidenceSummary.json",list(sources.values()))
    # Release only authored registries, not source identity/record maps or measurement values.
    atomic_json(out/"ComponentConceptRegistry.json",[o["payload"] for o in L.kinds["ComponentConcept"]])
    atomic_json(out/"MeasurementDefinitionRegistry.json",[dict(d,reference_status="NOT_QUALIFIED") for k,d in sorted(ds.items())])
    summary={"run_id":"B1-U2B-"+out.name,"contract_version":VERSION,"utc":when,"status":"PASS_BOUNDED_SEMANTIC_INTERPRETATION_AND_SHARED_BRIDGE",
             "upstream_u2a_objects":len(objs),"source_files_verified_before_after":len(resolver),"measurement_drafts_checked":len(ms),
             "measurement_status_counts":dict(stats),"missingness_counts":dict(miss),
             "component_concepts":len(cs),"measurement_definitions":len(ds),"definitions_with_real_selected_values":len(defs_used),
             "dictionary_only_definitions":len(ds)-len(defs_used),"authority_records":len(sources),"asa24_dictionary_fields_verified":len(sources["ASA_ITEMS"]["verified_field_rows"]),
             "quantity_interpretations":{"recipe_note_hold":recipe_count,"snapme_food_amount_reported_grams":snap_count,"snapme_duplicate_amount_fields_exact_equal":snap_equal},
             "representation_conversions":dict(conversions),"off_row_check":dict(off),"off_unit_discriminating_rows":off_discriminating,
             "native_namespaces":len(ns),"namespace_native_records":len(native_bindings),"source_key_bindings":len(keys),
             "same_namespace_key_duplicate_groups":sum(n>1 for n in key_counts.values()),
             "cross_namespace_identical_key_value_groups":sum(len(n)>1 for n in raw_to_namespaces.values()),
             "namespace_link_checks":dict(link_counts),"namespace_link_candidate_total":len(links),"namespace_equivalence_mappings_accepted":0,
             "new_typed_collections":{k:len(v) for k,v in sorted(L.kinds.items())},"new_typed_objects":len(loaded),"new_object_roundtrips":len(loaded),
             "d0_shared_bridge_roundtrips":len(back),"d0_historical_regressions_passed":d0["historical_test_passed"],
             "research_measurements_qualified":0,"research_releases":0,"global_b0_pass":False,"global_b1_frozen":False,
             "blockers":["NutriData original field dictionary, denominator, note unit and source-family evidence",
                         "OFF denominator per 100g vs 100mL; documentation conflict not empirically distinguished by selected rows",
                         "SNAPMe item grain and duplicate link semantics; do not aggregate",
                         "Nutrition5k independent incremental scan groups, food state, independent assay; N5k360 geometry held",
                         "external semantic mappings, unimplemented native adapters, full D0 migration and release qualification"]}
    atomic_json(out/"SemanticQualificationReport.json",summary)
    atomic_json(private/"collection_manifest.json",{p.name:{"sha256":file_sha(p),"bytes":p.stat().st_size,"rows":len(L.kinds[p.stem])} for p in tables.glob("*.jsonl")})
    print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--out",type=P.Path,required=True);a=p.parse_args();main(a.root,a.out)
