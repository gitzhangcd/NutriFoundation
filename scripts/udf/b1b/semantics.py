"""UDF U2-B bounded measurement semantics and namespace contract.

Policy definitions are authored/real-source-grounded mixed constructs, not experimental
observations. Raw values and historical U2-A records are never overwritten.
"""
from decimal import Decimal, InvalidOperation
import hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path
from contract import canon,digest,ref,ptr,require,ContractError,slot_value,pending,unavailable,na,validate_slot,raw_numeric_slot,namespace_of,resolve

VERSION="UDF-B1-SEMANTICS-DRAFT-0.1"
ND="nutridata:"
N5="fallback:Nutrition5k:"
SN="snapme:linkfile"
OFF="off:api_snapshot"
MENU="menumatch:menu"

# These are local conceptual identifiers; not FoodOn/FDC/chemical exact mappings.
# Separate unspecified and source-defined carbohydrate; do not conflate fat with fatty acid sum,
# sodium with salt, or food mass with a nutrient.
CONCEPTS={
 "ENERGY":("ENERGY","Declared food energy; method/source retained."),
 "FOOD_MASS":("PHYSICAL_QUANTITY","Food mass, distinct from nutrient content, portion volume, or ingested amount."),
 "PROTEIN_DECLARED":("NUTRIENT_AGGREGATE","Declared protein; analytical/calculation method not presumed equivalent."),
 "FAT_DECLARED":("NUTRIENT_AGGREGATE","Declared fat, without assuming method or total-fat definition."),
 "TOTAL_FAT_DECLARED":("NUTRIENT_AGGREGATE","Explicitly declared total fat."),
 "CARBOHYDRATE_UNSPECIFIED":("NUTRIENT_AGGREGATE","Carbohydrate definition not established as available versus total."),
 "CARBOHYDRATE_AVAILABLE":("NUTRIENT_AGGREGATE","Available carbohydrate excluding fibre according to source definition."),
 "CARBOHYDRATE_TOTAL":("NUTRIENT_AGGREGATE","Total carbohydrate; definition and method must be qualified."),
 "SODIUM":("CHEMICAL_ELEMENT_ATTRIBUTE","Sodium content; not salt mass."),
 "DIETARY_FIBER":("NUTRIENT_AGGREGATE","Declared dietary fiber; analytical method retained."),
 "VITAMIN_A_RAE":("BIOLOGICAL_EQUIVALENT","Retinol activity equivalents; not RE or retinol mass."),
 "VITAMIN_A_RE":("BIOLOGICAL_EQUIVALENT","Retinol equivalents; not RAE."),
 "FOLATE_TOTAL":("NUTRIENT_AGGREGATE","Total folate; not dietary folate equivalents."),
 "FOLIC_ACID":("CHEMICAL_FORM","Folic acid, distinct from food folate."),
 "FOLATE_FOOD":("NUTRIENT_AGGREGATE","Food folate, not folic acid or DFE."),
 "FOLATE_DFE":("BIOLOGICAL_EQUIVALENT","Dietary folate equivalents; no generic microgram conversion."),
 "GI":("FUNCTIONAL_MEASUREMENT","Glycaemic index; comparator/method required, not nutrient mass."),
 "NRV_PERCENT":("LABEL_REFERENCE_RATIO","Percentage of a versioned label reference value; not individual requirement."),
 "RECIPE_AMOUNT_UNSPECIFIED":("SOURCE_QUANTITY","Recipe note quantity; original unit and basis not established.")
}
ND_MAP={"能量":("ENERGY","kcal"),"蛋白质":("PROTEIN_DECLARED","g"),"脂肪":("FAT_DECLARED","g"),"碳水化合物":("CARBOHYDRATE_UNSPECIFIED","g"),"钠":("SODIUM","mg")}
N5_MAP={"energy":("ENERGY","kcal"),"mass":("FOOD_MASS","g"),"fat":("FAT_DECLARED","g"),"carb":("CARBOHYDRATE_UNSPECIFIED","g"),"protein":("PROTEIN_DECLARED","g")}
N5_ING={"cal/g":("ENERGY","kcal"),"fat(g)":("FAT_DECLARED","g"),"carb(g)":("CARBOHYDRATE_UNSPECIFIED","g"),"protein(g)":("PROTEIN_DECLARED","g")}
ASA={"FOODAMT":("FOOD_MASS","g"),"KCAL":("ENERGY","kcal"),"PROT":("PROTEIN_DECLARED","g"),"TFAT":("TOTAL_FAT_DECLARED","g"),"CARB":("CARBOHYDRATE_UNSPECIFIED","g"),"SODI":("SODIUM","mg"),"FIBE":("DIETARY_FIBER","g"),"VARA":("VITAMIN_A_RAE","ug_RAE"),"FOLA":("FOLATE_TOTAL","ug"),"FA":("FOLIC_ACID","ug"),"FF":("FOLATE_FOOD","ug"),"FDFE":("FOLATE_DFE","ug_DFE")}
OFF_MAP={"energy-kcal":("ENERGY","kcal"),"proteins":("PROTEIN_DECLARED","g"),"fat":("FAT_DECLARED","g"),"carbohydrates":("CARBOHYDRATE_AVAILABLE","g"),"sodium":("SODIUM","g")}
AUTH={
 "NDSF":"Nutrition Foundation v0.1 Part III 2.2-3.2",
 "UDF":"AI Nutri UDF v2.1 sections 11,15-22,34-37",
 "ND_PUBLIC":"https://www.nutridata.cn/",
 "N5_README":"https://github.com/google-research-datasets/Nutrition5k",
 "SN_PAPER":"https://pmc.ncbi.nlm.nih.gov/articles/PMC10708545/",
 "ASA_VERSION":"https://epi.grants.cancer.gov/asa24/respondent/2020.html",
 "ASA_ITEMS":"https://epi.grants.cancer.gov/asa24/researcher/ASA24_2020.zip#2020Record/DataDictionary_ITEMS_2020Record.xls",
 "OFF_SCHEMA":"https://openfoodfacts.github.io/documentation/docs/Product-Opener/schemas/schemas/product_nutrition/",
 "OFF_CONFLICT":"https://openfoodfacts.github.io/documentation/docs/Product-Opener/dev/explain-nutrition-data/",
 "MENU_README":"https://neelj.com/projects/menumatch/data/"
}
def numeric(x):
    if x is None or isinstance(x,bool):return None
    try:
        d=Decimal(str(x).strip())
        return d if d.is_finite() else None
    except (InvalidOperation,ValueError):return None
def missingness(raw):
    # Lexical class only. Numeric zero remains reported zero, not validated chemical zero.
    v=numeric(raw)
    if v is not None:
        return {"lexical_class":"REPORTED_NUMERIC_ZERO" if v==0 else "REPORTED_NUMERIC_NONZERO",
                "semantic_state":"SOURCE_NUMERIC_VALUE","quantity":slot_value(str(v)),
                "measured_zero_proved":False}
    if raw is None or (isinstance(raw,str) and not raw.strip()):
        return {"lexical_class":"EMPTY_OR_NULL","semantic_state":"SOURCE_VALUE_UNAVAILABLE",
                "quantity":unavailable("SOURCE_MISSING","raw token empty or null"),"measured_zero_proved":False}
    token=str(raw).strip()
    # Preserve trace spelling but no LOD or known detection semantics for this source.
    label={"tr":"TRACE_TOKEN_UNRESOLVED","—":"DASH_TOKEN_UNRESOLVED","-":"DASH_TOKEN_UNRESOLVED","…":"ELLIPSIS_TOKEN_UNRESOLVED","/":"SLASH_TOKEN_UNRESOLVED"}.get(token.lower(),"OTHER_TOKEN_UNRESOLVED")
    return {"lexical_class":label,"semantic_state":"PENDING_SOURCE_TOKEN_DEFINITION","quantity":pending("native token meaning/limit not verified"),"measured_zero_proved":False}
def ns_record(namespace,artifacts):
    ids=sorted(ref(a) for a in artifacts)
    role=sorted({a["payload"]["source_role"] for a in artifacts})
    namespace_id="ns:"+digest([namespace,sorted(a["payload"]["file_sha256"] for a in artifacts)])[:32]
    return {"namespace_id":namespace_id,"native_namespace":namespace,"snapshot_artifact_refs":ids,"source_roles":role,
            "scope":"SOURCE_SNAPSHOT_ONLY","qualification":"KEY_DOMAIN_IDENTIFIED_NOT_GLOBAL_ENTITY",
            "cross_source_identity":"HOLD_NO_EQUIVALENCE","origin_version_equivalence":"UNRESOLVED"}
def qualify_namespace(n,left,right,rule):
    require(left in n and right in n,"NAMESPACE_NOT_REGISTERED")
    allowed={
      ("nutridata:dish","nutridata:ingredient"):"BUSINESS_ID_AND_CODE",
      ("fallback:Nutrition5k:dish","fallback:Nutrition5k:ingredient"):"PADDED_INGREDIENT_ID",
      ("menumatch:labels","menumatch:menu"):"MENU_LABEL_KEY",
      ("epic100:train","epic100:verb_class"):"EPIC_VERB_KEY",
      ("epic100:train","epic100:noun_class"):"EPIC_NOUN_KEY",
      ("epic100:train","epic100:video_id"):"EPIC_VIDEO_KEY"}
    require(allowed.get((left,right))==rule,"CROSS_NAMESPACE_RELATION_UNQUALIFIED")
    return "STRUCTURAL_NATIVE_CANDIDATE_ONLY"
def identity_guard(left,right,relation):
    require(relation!="SAME_PHYSICAL_INSTANCE","INSTANCE_EQUIVALENCE_NOT_AUTHORIZED")
    require(left["namespace_id"]==right["namespace_id"],"CROSS_NAMESPACE_IDENTITY")
    require(left["key_domain"]==right["key_domain"],"KEY_DOMAIN_MISMATCH")
    return left["key_value"]==right["key_value"]
def missingness_guard(raw,interpreted):
    require(canon(missingness(raw))==canon(interpreted),"MISSINGNESS_PROMOTION")
def exact_component_mapping(a,b):
    require(a==b,"COMPONENT_DEFINITION_MISMATCH")
    # Even same local concept only identifies declared attribute family.
    return "SAME_DECLARED_COMPONENT_FAMILY_ONLY"
def mass_unit_transform(v,from_unit,to_unit):
    factors={"g":Decimal(1),"mg":Decimal("0.001"),"ug":Decimal("0.000001")}
    require(from_unit in factors and to_unit in factors,"INCOMPATIBLE_NUMERATOR_UNIT")
    x=numeric(v);require(x is not None,"NONNUMERIC_CONVERSION")
    return x*factors[from_unit]/factors[to_unit]
def conversion_guard(from_basis,to_basis,from_state,to_state,density=None,serving_mass=None):
    require(from_state==to_state and from_state not in ("UNKNOWN","PENDING"),"STATE_OR_PREPARATION_UNQUALIFIED")
    if from_basis==to_basis:return
    if {from_basis,to_basis}=={"PER_100G","PER_100ML"}:
        require(numeric(density) is not None and numeric(density)>0,"DENSITY_REQUIRED")
    elif {from_basis,to_basis}=={"PER_SERVING","PER_100G"}:
        require(numeric(serving_mass) is not None and numeric(serving_mass)>0,"SERVING_MASS_REQUIRED")
    else:raise ContractError("BASIS_CONVERSION_UNAUTHORIZED")
def qualified_calculation(definition,interpretation):
    require(definition["qualification"]=="SCIENCE_CALCULATION_QUALIFIED" and interpretation["qualification"]=="SCIENCE_CALCULATION_QUALIFIED","MEASUREMENT_CALCULATION_HOLD")
def definition_key(component_key):return "mdef:"+digest([VERSION,component_key])[:32]
def concept_id(k):return "cc:"+k
def definition(component_key,observed_unit=None):
    auth=[];grain="";unit=None;basis=None;status="HOLD_SOURCE_SEMANTICS";method="";blockers=[]
    if component_key=="nutridata:dish:major.note":
        c="RECIPE_AMOUNT_UNSPECIFIED";grain="SOURCE_RECIPE_LINE";method="Recipe note is numeric but unit, denominator and edible/cooked meaning unresolved.";auth=["ND_PUBLIC"];blockers=["NOTE_UNIT_UNCONFIRMED","INPUT_OUTPUT_BASIS_UNCONFIRMED"]
    elif component_key.startswith(ND):
        ns,k=component_key.rsplit(":",1)
        c,u=ND_MAP[k];unit=observed_unit or u
        require(unit==u,"NUTRIDATA_UNIT_CONFLICT")
        auth=["ND_PUBLIC"];grain="SOURCE_RECIPE_RECORD" if ns.endswith("dish") else "SOURCE_COMPOSITION_RECORD"
        method="Published platform attribute; original analytical or recipe calculation method unresolved."
        blockers=["NUTRIDATA_DENOMINATOR_UNCONFIRMED","FOOD_STATE_UNQUALIFIED","SOURCE_METHOD_UNQUALIFIED","SOURCE_FAMILY_UNRESOLVED"]
    elif component_key.startswith(N5+"ingredient:"):
        k=component_key[len(N5+"ingredient:"):];c,u=N5_ING[k]
        unit=u;basis="PER_GRAM_SOURCE_INGREDIENT";grain="SOURCE_INGREDIENT_REFERENCE"
        method="USDA-based per-gram source composition; not independently measured chemical value."
        auth=["N5_README"];status="SOURCE_FIELD_CONTRACT_SUPPORTED"
        blockers=["FOOD_STATE_UNQUALIFIED","SOURCE_FAMILY_UNRESOLVED","REFERENCE_NOT_QUALIFIED"]
    elif component_key.startswith(N5+"dish:"):
        k=component_key[len(N5+"dish:"):];line=k.startswith("ingredient:")
        if line:k=k.split(":",1)[1]
        c,u=N5_MAP[k];unit=u;basis="SOURCE_INGREDIENT_LINE_TOTAL" if line else "SOURCE_SCAN_TOTAL";grain="SOURCE_SCAN_INGREDIENT_LINE" if line else "SOURCE_SCAN"
        method="Source-reported weighed mass candidate." if k=="mass" else "Source-reported USDA-based composition total, not independent assay."
        auth=["N5_README"];status="SOURCE_FIELD_CONTRACT_SUPPORTED"
        blockers=["SCAN_DEPENDENCY_GROUP_UNVERIFIED","REFERENCE_NOT_QUALIFIED"]
    elif component_key.startswith(SN+":"):
        k=component_key.split(":")[-1];c,u=ASA[k];unit=u;basis="SOURCE_REPORTED_ITEM_LINK_ROW";grain="PHOTO_LINKED_ASA24_ITEM_ROW"
        method="ASA24-2020 food record and database-derived amount/nutrient attribute; photo linkage not unique intake event."
        auth=["SN_PAPER","ASA_VERSION","ASA_ITEMS"];status="SOURCE_FIELD_CONTRACT_SUPPORTED"
        blockers=["INTAKE_EVENT_KEY_UNQUALIFIED","NO_AGGREGATION","REPORTED_NOT_WEIGHED","REFERENCE_NOT_QUALIFIED"]
    elif component_key.startswith(OFF+":"):
        k=component_key.split(":")[-1];c,u=OFF_MAP[k];unit=u
        basis=None;grain="AS_SOLD_PRODUCT_LABEL_API_VALUE"
        method="OFF product-nutrition schema standard numerator; developer note disagrees; verify row against native entered amount when possible."
        auth=["OFF_SCHEMA","OFF_CONFLICT"];status="SOURCE_NUMERATOR_CONTRACT_SUPPORTED_BASIS_HOLD"
        blockers=["PER_100G_VS_100ML_UNRESOLVED","DOC_CONFLICT_REQUIRES_ROW_CHECK","LABEL_REFERENCE_NOT_ASSAY","REFERENCE_NOT_QUALIFIED"]
    elif component_key==MENU+":calories":
        c="ENERGY";unit=observed_unit or "kcal";grain="MENU_ITEM_REFERENCE"
        method="Menu-listed energy reference; portion denominator not established."
        auth=["MENU_README"];blockers=["MENU_PORTION_DENOMINATOR_UNCONFIRMED","NOT_INTAKE","REFERENCE_NOT_QUALIFIED"]
    else:raise ContractError("COMPONENT_KEY_UNREGISTERED")
    return {"measurement_definition_id":definition_key(component_key),"concept_key":component_key,"component_ref":concept_id(c),"value_type":"NUMBER",
            "unit":slot_value(unit) if unit else pending("source unit unresolved"),
            "basis":slot_value(basis) if basis else pending("OFF suffix may denote per 100 g or 100 mL; specific denominator unresolved" if component_key.startswith(OFF+":") else "denominator unresolved"),
            "method":method,"reference_window":"SOURCE_REPORTED_DAY_NOT_HABITUAL" if component_key.startswith(SN+":") else "SOURCE_SNAPSHOT_OR_SCAN_NOT_LONGITUDINAL",
            "aggregation":grain,"error_model":pending("no independent error model"),"reliability":pending("not empirically estimated"),
            "validity":pending("field interpretation not scientific measurement validity"),
            "cost_definition":na("measurement-cost task not activated"),
            "leakage_risk":"development exposed; no locked evaluation or future training",
            "authority_keys":auth,"qualification":status,"blockers":blockers}
def validate_definition(d):
    fields={"measurement_definition_id","concept_key","component_ref","value_type","unit","basis","method","reference_window","aggregation","error_model","reliability","validity","cost_definition","leakage_risk","authority_keys","qualification","blockers"}
    require(set(d)==fields,"MEASUREMENT_DEFINITION_FIELDS")
    require(d["measurement_definition_id"]==definition_key(d["concept_key"]),"DEFINITION_ID")
    require(d["component_ref"] in {concept_id(k) for k in CONCEPTS},"COMPONENT_REF")
    for k in ("unit","basis","error_model","reliability","validity","cost_definition"):validate_slot(d[k])
    for k in ("method","reference_window","aggregation","leakage_risk"):require(isinstance(d[k],str) and bool(d[k].strip()),"DEFINITION_TEXT")
    require(d["authority_keys"] and all(k in AUTH for k in d["authority_keys"]),"AUTHORITY_MISSING")
    require(d["qualification"]!="SCIENCE_CALCULATION_QUALIFIED" and d["validity"]["tag"]=="PENDING","SCIENCE_QUALIFICATION_INFLATION")
    require(canon(d)==canon(definition(d["concept_key"])),"DEFINITION_POLICY_DRIFT")
def off_row_check(native,k):
    # Check source-entered vs standardized numerator only for rows declared 100g,
    # with explicit source-entered unit. No inferred g vs ml denominator.
    n=native["nutriments"];v=numeric(n.get(k+"_100g"));e=numeric(n.get(k+"_value"))
    u=n.get(k+"_unit");target=OFF_MAP[k][1]
    if native.get("nutrition_data_per")!="100g" or v is None or e is None or not isinstance(u,str):
        return {"status":"HOLD_ROW_UNIT_CHECK_UNAVAILABLE","original_display_unit":u}
    try:
        if target=="kcal":
            if u=="kcal":converted=e
            elif u=="kJ":converted=e/Decimal("4.184")
            else:raise ContractError("OFF_ENERGY_UNIT")
        else:
            converted=mass_unit_transform(e,{"µg":"ug","μg":"ug","mcg":"ug"}.get(u,u),target)
    except ContractError:return {"status":"HOLD_ROW_UNIT_CHECK_UNAVAILABLE","original_display_unit":u}
    # This is a representation-level check with an explicit exploratory tolerance;
    # source rounding/precision still unknown. No physical measurement claim.
    diff=abs(converted-v);tol=max(Decimal("0.000001"),abs(v)*Decimal("0.000001"))
    return {"status":"ROW_NUMERATOR_CONSISTENT" if diff<=tol else "HOLD_ROW_NUMERATOR_DISAGREEMENT","original_display_unit":u,"tolerance":"max(1e-6, abs(value)*1e-6)","abs_difference":str(diff)}
def interpret_measurement(o,idx,d):
    p=o["payload"];native=resolve(idx,p["native_ref"],"NativeRecord")["payload"]["raw"];raw=p["bindings"]["value"]["raw_value"]
    mi=missingness(raw);unit=d["unit"];basis=d["basis"];status=d["qualification"];rowcheck=None;conversion=None
    if p["component_key"].startswith(OFF+":"):
        k=p["component_key"].split(":")[-1];rowcheck=off_row_check(native,k)
        if rowcheck["status"]!="ROW_NUMERATOR_CONSISTENT":
            unit=pending("OFF numerator row check not established")
            status="HOLD_OFF_NUMERATOR_ROW_CHECK"
    # Per-gram -> per-100g representation of the same source ingredient reference,
    # not an approved normalized food value; no cross-source equivalence.
    if numeric(raw) is not None and numeric(raw)<0:
        status="HOLD_NEGATIVE_QUANTITY"
    if p["component_key"].startswith(N5+"ingredient:") and numeric(raw) is not None and numeric(raw)>=0:
        conversion={"operation":"SAME_SOURCE_DENOMINATOR_SCALE_1G_TO_100G","input":str(numeric(raw)),
                    "factor":"100","value":str(numeric(raw)*Decimal(100)),"numerator_unit":unit["value"],
                    "output_basis":"PER_100G_SAME_SOURCE_INGREDIENT_REFERENCE","qualification":"REPRESENTATION_ONLY",
                    "origin_mode":"DERIVED","construction_class":"DRV"}
    if p["component_key"]==SN+":SODI" and numeric(raw) is not None and numeric(raw)>=0:
        conversion={"operation":"SAME_SOURCE_NUMERATOR_MG_TO_G","input":str(numeric(raw)),
                    "factor":"0.001","value":str(mass_unit_transform(raw,"mg","g")),"numerator_unit":"g",
                    "output_basis":"SOURCE_REPORTED_ITEM_LINK_ROW","qualification":"REPRESENTATION_ONLY",
                    "origin_mode":"DERIVED","construction_class":"DRV"}
    return {"source_measurement_ref":ref(o),"source_native_ref":p["native_ref"],"measurement_definition_ref":d["measurement_definition_id"],
            "source_raw":raw,"missingness":mi,"interpretation_unit":unit,"interpretation_basis":basis,
            "field_semantics_status":status,"reference_profile":p["reference_profile"],"off_row_check":rowcheck,
            "conversion":conversion,"qualification":"HOLD_NOT_SCIENTIFICALLY_QUALIFIED","normalized_food_value":pending("no cross-source qualification"),
            "purpose":"CURATION_DEV_ONLY"}
def validate_interpretation(o,idx,d,i):
    require(i["source_measurement_ref"]==ref(o) and i["measurement_definition_ref"]==d["measurement_definition_id"],"INTERPRETATION_REF")
    require(canon(interpret_measurement(o,idx,d))==canon(i),"INTERPRETATION_DRIFT")
    missingness_guard(i["source_raw"],i["missingness"])
    require(i["qualification"]=="HOLD_NOT_SCIENTIFICALLY_QUALIFIED","SCIENCE_QUALIFICATION_INFLATION")
def qline(raw,unit,basis):
    # Note is not a measured zero or grams; only lexical amount interpretation.
    require(unit["tag"]=="PENDING" and basis["tag"]=="PENDING","RECIPE_NOTE_UNIT_BASIS_HOLD")
    return missingness(raw)
