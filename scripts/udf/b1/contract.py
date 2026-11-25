"""B1/U2-A development-only source-native contract; Python 3.9+ stdlib.
Extends UDF v2.1, not the existing NDF-D0 runtime. No release authorization.
"""
import copy
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

VERSION = "UDF-B1-NATIVE-DRAFT-0.1"
INSTANCE_CLASSES = {"REAL_SOURCE_GROUNDED", "MIXED_CONSTRUCTED", "SYNTHETIC", "SIMULATED"}
SOURCE_CLASSES = {"REAL_DATA", "REAL_DOCUMENT", "NATIVE_JUDGMENT", "SYNTHETIC_TEXT", "SIMULATED_EVENT"}
SCI_KINDS = ("SourceArtifact","SourceAnchor","StudyIdentity","EvidenceUnit","ScientificClaim","ScientificRelation","EvidenceConflict","EvidenceGap","VerificationRecord","KnowledgeSnapshot","ScientificReferenceState")
# Keep distinct record kinds/collections. Only SourceArtifact and SourceAnchor are instantiated here.
SCIENTIFIC_DELEGATED = SCI_KINDS[2:]
PAYLOAD_FIELDS = {
 "SourceArtifact": {"namespace","file_sha256","bytes","source_role","version_status"},
 "SourceAnchor": {"source_ref","locator","integrity","content","source_class"},
 "NativeRecord": {"artifact_ref","anchor_ref","locator","raw","raw_sha256","native_format","grain"},
 "FoodLabelDraft": {"native_ref","bindings","label_namespace","label_role"},
 "FoodEntityDraft": {"native_ref","bindings","entity_type","identity_scope"},
 "FoodInstanceDraft": {"native_ref","bindings","instance_scope","identity_status"},
 "RecipeDraft": {"native_ref","bindings","recipe_scope","quantity_semantics"},
 "RecipeIngredientDraft": {"native_ref","bindings","recipe_ref","quantity","unit","basis","parent_ref","link_status"},
 "NutrientMeasurementDraft": {"native_ref","bindings","subject_ref","component_key","original_value","original_unit","original_basis","normalized_value","preparation","source_method","reference_profile","qualification"},
 "DietaryObservationDraft": {"native_ref","bindings","identity_scope","observation_window","measurement_role","aggregation_status"},
 "MediaObservationDraft": {"native_ref","bindings","annotation_kind","media_identity_status"},
 "ProcessObservationDraft": {"native_ref","bindings","event_role","time_basis"},
 "ProcessVocabularyDraft": {"native_ref","bindings","label_namespace","vocabulary_role"},
 "VideoMetadataDraft": {"native_ref","bindings","media_scope","time_basis"},
 "QARecordDraft": {"native_ref","bindings","exposure_status"},
 "ProductVersionDraft": {"native_ref","bindings","product_identity_status","nutrition_basis"},
 "NativeLinkDraft": {"native_ref","bindings","relation_type","left_ref","right_ref","status","semantic_qualification"},
}
HEX64 = re.compile(r"^[a-f0-9]{64}$")
class ContractError(ValueError):
    pass
def require(ok, code):
    if not ok: raise ContractError(code)
def canon(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",",":"), allow_nan=False)
def digest(x):
    return hashlib.sha256(canon(x).encode("utf-8")).hexdigest()
def text_hash(b):
    return hashlib.sha256(b).hexdigest()
def nonblank(x):
    return isinstance(x,str) and bool(x.strip())
def slot_value(x):
    require(x is not None, "SLOT_VALUE_NULL")
    return {"tag":"VALUE","value":x}
def pending(reason):
    require(nonblank(reason),"MISSING_REASON")
    return {"tag":"PENDING","reason":reason}
def unavailable(reason,detail):
    return {"tag":"UNAVAILABLE","reason":reason,"detail":detail}
def na(reason):
    return {"tag":"NOT_APPLICABLE","reason":reason,"policy_ref":VERSION}
def validate_slot(s):
    require(isinstance(s,dict),"UNTAGGED_SLOT")
    t=s.get("tag")
    if t=="VALUE":
        require(set(s)=={"tag","value"} and s["value"] is not None,"SLOT_VALUE_NULL_OR_EXTRAS")
    elif t=="PENDING":
        require(set(s)=={"tag","reason"} and nonblank(s["reason"]),"SLOT_PENDING_INVALID")
    elif t=="UNAVAILABLE":
        require(set(s)=={"tag","reason","detail"} and nonblank(s["reason"]) and nonblank(s["detail"]),"SLOT_UNAVAILABLE_INVALID")
    elif t=="NOT_APPLICABLE":
        require(set(s)=={"tag","reason","policy_ref"} and nonblank(s["reason"]) and nonblank(s["policy_ref"]),"SLOT_NA_INVALID")
    else: raise ContractError("UNKNOWN_SLOT_TAG")
def raw_numeric_slot(raw):
    # This is lexical parsing only: a numeric 0 is not asserted to be measured zero.
    if raw is None or (isinstance(raw,str) and not raw.strip()):
        return unavailable("SOURCE_MISSING","source token empty or null; original retained")
    if isinstance(raw,bool):
        return unavailable("UNKNOWN_REASON","boolean is not a numeric measurement")
    try:
        d=Decimal(str(raw).strip())
        if not d.is_finite(): raise InvalidOperation()
        return slot_value(str(d))
    except (InvalidOperation,ValueError):
        return pending("source token semantics unresolved; original retained")
def ptr(data,path):
    require(isinstance(path,str) and (path=="" or path.startswith("/")),"INVALID_POINTER")
    v=data
    if path=="":return v
    for s in path[1:].split("/"):
        s=s.replace("~1","/").replace("~0","~")
        try:
            if isinstance(v,list):
                require(s.isdigit() and (s=="0" or not s.startswith("0")),"INVALID_INDEX")
                v=v[int(s)]
            elif isinstance(v,dict):v=v[s]
            else:raise KeyError(s)
        except (KeyError,IndexError,TypeError):raise ContractError("SOURCE_POINTER_UNRESOLVED")
    return v
def esc(s):return str(s).replace("~","~0").replace("/","~1")
def binding(raw,path,role="SOURCE_REPRESENTATION"):
    v=copy.deepcopy(ptr(raw,path))
    return {"path":path,"raw_value":v,"origin_mode":"OBSERVED","knowledge_state":"UNKNOWN" if v is None or v=="" else "KNOWN","construction_class":"OBS","visibility_overlay":"ROLE_RESTRICTED","role":role}
def ref(o):return o["object_id"]+"@"+o["revision_id"]
def create(kind,oid,payload,when,prov=(),deps=(),source_class="REAL_DATA",instance="REAL_SOURCE_GROUNDED"):
    o={"object_id":oid,"kind":kind,"schema_version":VERSION,"contract_version":VERSION,"lifecycle":"DRAFT","producer_role":"B1_SOURCE_ADAPTER","created_time":when,"clock_axis":"AUDIT_UTC","provenance_refs":list(prov),"dependency_refs":list(deps),"source_class":source_class,"instance_class":instance,"purpose_release_ref":pending("CURATION_DEV only; no release exists"),"purpose":"CURATION_DEV","supersedes_ref":na("first draft revision"),"payload":copy.deepcopy(payload)}
    o["revision_id"]=digest(o)
    return o
def verify_revision(o):
    x=dict(o);revision=x.pop("revision_id",None)
    require(isinstance(revision,str) and revision==digest(x),"REVISION_INTEGRITY")
def validate_base(o):
    required={"object_id","revision_id","kind","schema_version","contract_version","lifecycle","producer_role","created_time","clock_axis","provenance_refs","dependency_refs","source_class","instance_class","purpose_release_ref","purpose","supersedes_ref","payload"}
    require(set(o)==required,"ENVELOPE_FIELDS")
    require(o["schema_version"]==VERSION and o["contract_version"]==VERSION,"CONTRACT_VERSION")
    require(nonblank(o["object_id"]) and "@" not in o["object_id"],"OBJECT_ID")
    require(o["instance_class"] in INSTANCE_CLASSES,"INSTANCE_CLASS")
    require(o["source_class"] in SOURCE_CLASSES,"SOURCE_CLASS")
    require(not (o["instance_class"]=="REAL_SOURCE_GROUNDED" and o["source_class"] in {"SYNTHETIC_TEXT","SIMULATED_EVENT"}),"REAL_WITH_SYNTHETIC_SOURCE")
    require(o["instance_class"]=="REAL_SOURCE_GROUNDED","REAL_ONLY_PROFILE")
    require(o["lifecycle"]=="DRAFT" and o["purpose"]=="CURATION_DEV","DEV_ONLY")
    require(o["clock_axis"]=="AUDIT_UTC","CLOCK_AXIS")
    try:dt=datetime.fromisoformat(o["created_time"]);require(dt.tzinfo is not None,"TIMEZONE_REQUIRED")
    except (TypeError,ValueError):raise ContractError("INVALID_CREATED_TIME")
    for k in ("provenance_refs","dependency_refs"):
        require(isinstance(o[k],list) and all(nonblank(r) and "@" in r for r in o[k]) and len(set(o[k]))==len(o[k]),"IMMUTABLE_REFS")
    validate_slot(o["purpose_release_ref"]);validate_slot(o["supersedes_ref"])
    require(o["purpose_release_ref"]["tag"]=="PENDING","UNAUTHORIZED_RELEASE")
    require(o["kind"] in PAYLOAD_FIELDS,"KIND_NOT_IMPLEMENTED")
    require(isinstance(o["payload"],dict) and set(o["payload"])==PAYLOAD_FIELDS[o["kind"]],"TYPED_PAYLOAD_FIELDS")
    verify_revision(o)
def resolve(index,r,kind):
    require(isinstance(r,str) and r in index,"UNRESOLVED_REF")
    o=index[r]
    require(o["kind"] in (kind if isinstance(kind,tuple) else (kind,)),"REF_KIND_MISMATCH")
    return o
def require_release(o,requested):
    require(requested=="CURATION_DEV" and o["purpose"]=="CURATION_DEV","RELEASE_BLOCKED")
    require(o["instance_class"]=="REAL_SOURCE_GROUNDED","REAL_ONLY_PROFILE")
def validate_relation(rel, left, right, same_namespace, evidence):
    if rel=="SAME_PHYSICAL_INSTANCE":
        require(same_namespace and evidence=="NATIVE_INSTANCE_KEY_VERIFIED","INSTANCE_IDENTITY_NOT_PROVED")
    if rel=="NATIVE_CANDIDATE_LINK":
        require(evidence in {"BUSINESS_ID_CODE","EXPLICIT_NATIVE_ID_TRANSFORM","DECLARED_NATIVE_LABEL_KEY"},"LINK_EVIDENCE_INVALID")
def validate_measurement_use(m,operation="CALCULATE"):
    for k in ("original_value","original_unit","original_basis","normalized_value","preparation","source_method","qualification"):
        validate_slot(m[k])
    if operation=="CALCULATE":
        require(all(m[k]["tag"]=="VALUE" for k in ("original_value","original_unit","original_basis","normalized_value","preparation","source_method","qualification")),"MEASUREMENT_NOT_QUALIFIED")
        require(m["qualification"]["value"]=="QUALIFIED_FOR_CALCULATION","MEASUREMENT_NOT_QUALIFIED")
    if operation=="CHEMICAL_ASSAY_CLAIM":
        require(m["reference_profile"]=="Q-ASSAY_QUALIFIED","REFERENCE_PROFILE_MISMATCH")
def conversion_guard(from_unit,to_unit,from_state,to_state,density=None,portion_mass=None):
    if from_state!=to_state or "UNKNOWN" in (from_state,to_state):raise ContractError("FOOD_STATE_INCOMPARABLE")
    if {from_unit,to_unit}=={"mL","g"}:require(density is not None and density>0,"DENSITY_REQUIRED")
    if "serving" in (from_unit,to_unit) and from_unit!=to_unit:require(portion_mass is not None and portion_mass>0,"PORTION_MASS_REQUIRED")
def independent_sources(source_families):
    require(all(nonblank(s) for s in source_families) and len(set(source_families))==len(source_families),"SOURCE_DEPENDENCE")
def verify_geometry(scale_slot,group_verified):
    validate_slot(scale_slot)
    require(scale_slot["tag"]=="VALUE" and group_verified,"GEOMETRY_OR_GROUP_HOLD")
def require_aggregation(grain,unique_record_keys,source_measurement_keys,qualified=False):
    require(qualified and grain=="SOURCE_FOOD_RECORD","AGGREGATION_NOT_QUALIFIED")
    require(len(set(unique_record_keys))==len(unique_record_keys) and len(set(source_measurement_keys))==len(source_measurement_keys),"DUPLICATE_AGGREGATION")
def require_reference(owner,qualification,profile):
    require(owner=="INDEPENDENT_QUALIFIED_REVIEW" and qualification=="QUALIFIED" and nonblank(profile),"REFERENCE_NOT_QUALIFIED")
def require_locked_probe(exposed,private,group_verified,freeze_before_training):
    require(not exposed and private and group_verified and freeze_before_training,"PROBE_NOT_INDEPENDENT")
def dev_projection(o,task="SCHEMA_INSPECTION"):
    # Allowlist-only structural view. No private values, IDs, source locators, filenames or hashes.
    require(task=="SCHEMA_INSPECTION" and o["purpose"]=="CURATION_DEV","PROJECTION_NOT_AUTHORIZED")
    require(o["kind"] in PAYLOAD_FIELDS,"KIND_NOT_IMPLEMENTED")
    out={"kind":o["kind"],"schema_version":VERSION,"task":"SCHEMA_INSPECTION","field_names":sorted(PAYLOAD_FIELDS[o["kind"]])}
    validate_dev_projection(out)
    return out
def validate_dev_projection(out):
    require(set(out)=={"kind","schema_version","task","field_names"} and out["task"]=="SCHEMA_INSPECTION" and out["schema_version"]==VERSION,"PROJECTION_CLOSURE")
    require(out["kind"] in PAYLOAD_FIELDS and out["field_names"]==sorted(PAYLOAD_FIELDS[out["kind"]]),"PROJECTION_CLOSURE")
def namespace_of(idx,o):
    n=resolve(idx,o["payload"]["native_ref"],"NativeRecord")
    a=resolve(idx,n["payload"]["artifact_ref"],"SourceArtifact")
    return a["payload"]["namespace"]
def validate_set(objects):
    idx={}
    for o in objects:
        validate_base(o)
        r=ref(o);require(r not in idx,"DUPLICATE_REVISION")
        idx[r]=o
    native_ids=set()
    for r,o in idx.items():
        p=o["payload"];kind=o["kind"]
        for rr in o["provenance_refs"]+o["dependency_refs"]:
            require(rr in idx,"UNRESOLVED_REF")
            require(rr!=r,"SELF_REFERENCE")
            if o["instance_class"]=="REAL_SOURCE_GROUNDED":
                require(idx[rr]["instance_class"]=="REAL_SOURCE_GROUNDED","REAL_DEPENDS_ON_NONREAL")
        if kind=="SourceArtifact":
            require(nonblank(p["namespace"]) and isinstance(p["bytes"],int) and p["bytes"]>0 and isinstance(p["file_sha256"],str) and HEX64.fullmatch(p["file_sha256"]),"ARTIFACT_INVALID")
        elif kind=="SourceAnchor":
            a=resolve(idx,p["source_ref"],"SourceArtifact")
            require(p["source_ref"] in o["provenance_refs"],"MISSING_ANCHOR_PROVENANCE")
            require(p["source_class"]==o["source_class"] and p["integrity"]==a["payload"]["file_sha256"],"ANCHOR_INTEGRITY")
            validate_slot(p["content"])
        elif kind=="NativeRecord":
            a=resolve(idx,p["artifact_ref"],"SourceArtifact");b=resolve(idx,p["anchor_ref"],"SourceAnchor")
            require(p["anchor_ref"] in o["provenance_refs"] and p["artifact_ref"] in o["dependency_refs"],"NATIVE_PROVENANCE")
            require(b["payload"]["source_ref"]==p["artifact_ref"] and b["payload"]["locator"]==p["locator"],"ANCHOR_MISMATCH")
            require(digest(p["raw"])==p["raw_sha256"],"NATIVE_RAW_DIGEST")
            k=(p["artifact_ref"],canon(p["locator"]));require(k not in native_ids,"DUPLICATE_NATIVE_LOCATOR");native_ids.add(k)
        else:
            n=resolve(idx,p["native_ref"],"NativeRecord")
            require(p["native_ref"] in o["dependency_refs"] and n["payload"]["anchor_ref"] in o["provenance_refs"],"CANONICAL_PROVENANCE")
            require(isinstance(p["bindings"],dict) and bool(p["bindings"]),"MISSING_BINDINGS")
            for name,b in p["bindings"].items():
                require(nonblank(name) and set(b)=={"path","raw_value","origin_mode","knowledge_state","construction_class","visibility_overlay","role"},"BINDING_FIELDS")
                require(canon(ptr(n["payload"]["raw"],b["path"]))==canon(b["raw_value"]),"CANONICAL_SOURCE_DRIFT")
                require(b["origin_mode"]=="OBSERVED" and b["construction_class"]=="OBS" and b["visibility_overlay"]=="ROLE_RESTRICTED","FIELD_AXES")
                require(b["knowledge_state"]==("UNKNOWN" if b["raw_value"] is None or b["raw_value"]=="" else "KNOWN"),"FIELD_KNOWLEDGE_STATE")
            if kind=="RecipeIngredientDraft":
                recipe=resolve(idx,p["recipe_ref"],"RecipeDraft")
                require(recipe["payload"]["native_ref"]==p["native_ref"] and p["recipe_ref"] in o["dependency_refs"],"RECIPE_SOURCE_MISMATCH")
                require(namespace_of(idx,o)=="nutridata:dish","RECIPE_SCOPE_MISMATCH")
                for k in ("quantity","unit","basis","parent_ref"):validate_slot(p[k])
                require(p["unit"]["tag"]=="PENDING" and p["basis"]["tag"]=="PENDING","RECIPE_NOTE_UNIT_BASIS_HOLD")
                require(canon(p["quantity"])==canon(raw_numeric_slot(p["bindings"]["amount"]["raw_value"])),"RECIPE_QUANTITY_DRIFT")
                if p["parent_ref"]["tag"]=="VALUE":
                    parent=resolve(idx,p["parent_ref"]["value"],"FoodEntityDraft")
                    require(p["parent_ref"]["value"] in o["dependency_refs"],"MISSING_PARENT_DEPENDENCY")
                    require(p["link_status"]=="CANDIDATE_ID_AND_CODE","RECIPE_LINK_STATUS")
                    require(namespace_of(idx,parent)=="nutridata:ingredient","PARENT_NAMESPACE_MISMATCH")
                    pb=parent["payload"]["bindings"];lb=p["bindings"]
                    require(str(lb["ingredient_id"]["raw_value"])==str(pb["business_id"]["raw_value"]) and lb["code"]["raw_value"]==pb["code"]["raw_value"],"BUSINESS_KEY_CODE_MISMATCH")
                else:require(p["link_status"]=="HOLD_UNMATCHED_OR_CONFLICT","RECIPE_LINK_STATUS")
            elif kind=="NutrientMeasurementDraft":
                subject=resolve(idx,p["subject_ref"],("FoodEntityDraft","FoodInstanceDraft","RecipeDraft","MediaObservationDraft","ProductVersionDraft","DietaryObservationDraft","RecipeIngredientDraft"))
                require(p["subject_ref"] in o["dependency_refs"] and subject["payload"]["native_ref"]==p["native_ref"],"MEASUREMENT_SUBJECT_MISMATCH")
                for k in ("original_value","original_unit","original_basis","normalized_value","preparation","source_method","qualification"):validate_slot(p[k])
                require(canon(p["original_value"])==canon(raw_numeric_slot(p["bindings"]["value"]["raw_value"])),"MEASUREMENT_VALUE_DRIFT")
                require(p["normalized_value"]["tag"]=="PENDING" and p["qualification"]["tag"]=="PENDING","UNQUALIFIED_NORMALIZATION")
                require(p["reference_profile"] in {"Q-COMPOSITION_SOURCE_UNQUALIFIED","Q-COMMON-CALC_CANDIDATE","Q-MASS_CANDIDATE","Q-RECALL_CANDIDATE","Q-LABEL_CANDIDATE","Q-MENU_CANDIDATE"},"REFERENCE_PROFILE_MISMATCH")
                ns=namespace_of(idx,o)
                require(p["component_key"].startswith(ns+":"),"COMPONENT_NAMESPACE")
                if ns.startswith("nutridata:"):
                    require(p["original_basis"]["tag"]=="PENDING" and p["source_method"]["tag"]=="PENDING","SOURCE_BASIS_HOLD")
                    unit=p["bindings"]["unit"]["raw_value"]
                    require(p["original_unit"]==slot_value(unit) if unit else p["original_unit"]["tag"]=="PENDING","SOURCE_UNIT_DRIFT")
                if ns=="off:api_snapshot":
                    require(p["original_unit"]["tag"]=="PENDING","OFF_UNIT_UNQUALIFIED")
            elif kind=="NativeLinkDraft":
                left=resolve(idx,p["left_ref"],("RecipeDraft","FoodInstanceDraft","MediaObservationDraft","ProcessObservationDraft","RecipeIngredientDraft"))
                right=resolve(idx,p["right_ref"],("FoodEntityDraft","ProcessVocabularyDraft","VideoMetadataDraft"))
                require(p["relation_type"]=="NATIVE_CANDIDATE_LINK" and p["status"]=="STRUCTURALLY_MATCHED" and p["semantic_qualification"]=="PENDING","LINK_PROMOTION")
                require(p["left_ref"] in o["dependency_refs"] and p["right_ref"] in o["dependency_refs"],"LINK_DEPENDENCY")
                require(left["payload"]["native_ref"]==p["native_ref"],"LINK_SOURCE_MISMATCH")
                a=p["bindings"]["source_key"]["raw_value"];b=right["payload"]["bindings"]["business_id"]["raw_value"]
                lns=namespace_of(idx,left);rns=namespace_of(idx,right)
                if left["kind"]=="FoodInstanceDraft":
                    require(lns=="fallback:Nutrition5k:dish" and rns=="fallback:Nutrition5k:ingredient","LINK_NAMESPACE_MISMATCH")
                    require(str(b).isdigit() and a=="ingr_"+str(b).zfill(10),"NATIVE_ID_TRANSFORM_MISMATCH")
                else:
                    if lns=="epic100:train":
                        require(rns=="epic100:"+p["bindings"]["source_key"]["path"].split("/")[-1],"LINK_NAMESPACE_MISMATCH")
                        require(right["kind"]==("VideoMetadataDraft" if rns=="epic100:video_id" else "ProcessVocabularyDraft"),"REF_KIND_MISMATCH")
                    else:require(lns=="menumatch:labels" and rns=="menumatch:menu","LINK_NAMESPACE_MISMATCH")
                    require(str(a)==str(b),"NATIVE_LABEL_KEY_MISMATCH")
            elif kind=="FoodEntityDraft":
                require(p["identity_scope"]=="SOURCE_SCOPED_ONLY","CONCEPT_IDENTITY_PROMOTION")
            elif kind=="FoodInstanceDraft":
                require(p["instance_scope"]=="NUTRITION5K_SCAN" and p["identity_status"]=="NATIVE_SCAN_ONLY_GROUP_UNRESOLVED","INSTANCE_IDENTITY_NOT_PROVED")
            elif kind=="DietaryObservationDraft":
                require(p["aggregation_status"]=="HOLD_DUPLICATE_GRAIN_UNRESOLVED" and p["observation_window"]=="SOURCE_REPORTED_DAY_NOT_HABITUAL" and p["identity_scope"]=="SOURCE_PRIVATE_NAMESPACE_ONLY","DIETARY_STATE_INFLATION")
            elif kind=="QARecordDraft":
                require(p["exposure_status"]=="DEVELOPMENT_EXPOSED","EXPOSURE_STATE")
    return idx
