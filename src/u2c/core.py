"""U2-C versioned development contract core.
Legacy run objects are immutable inputs. New effective views are separate revisions;
immutable old refs are resolved through a verified legacy registry, not rewritten.
No measurement, mapping, reference or training release is authorized by this module.
"""
import copy, hashlib, json, re, unicodedata
from decimal import Decimal, InvalidOperation
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from collections import Counter
from jsonschema import Draft202012Validator, FormatChecker
VERSION="UDF-U2C-ENVELOPE-0.1"
class ContractError(ValueError):pass
def require(ok,code):
    if not ok:raise ContractError(code)
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def digest(x):return hashlib.sha256(canon(x).encode("utf8")).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def blob(path):
    b=path.read_bytes();return hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
def ref(o):return o["object_id"]+"@"+o["revision_id"]
def seal(o):
    o.pop("revision_id",None);o["revision_id"]=digest(o);return o
def revision_ok(o):
    x=dict(o);h=x.pop("revision_id",None);require(h==digest(x),"REVISION_INTEGRITY")
def load(p):return json.loads(p.read_text(encoding="utf8"))
def lines(p):
    with p.open(encoding="utf8") as f:
        for l in f:yield json.loads(l)
def put(p,o):
    with p.open("x",encoding="utf8") as f:json.dump(o,f,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
def val(x):return {"tag":"VALUE","value":x}
def pending(s):return {"tag":"PENDING","reason":s}
def na(s):return {"tag":"NOT_APPLICABLE","reason":s,"policy_ref":VERSION}
def number(x):
    if x is None or isinstance(x,bool):return None
    try:
        d=Decimal(str(x).strip());return d if d.is_finite() else None
    except (InvalidOperation,ValueError):return None
def pointer(raw,path):
    require(isinstance(path,str) and (path=="" or path.startswith("/")),"INVALID_POINTER")
    for k in path[1:].split("/") if path else []:
        k=k.replace("~1","/").replace("~0","~")
        try:
            if isinstance(raw,list):
                require(k.isdigit() and (k=="0" or not k.startswith("0")),"INVALID_POINTER")
                raw=raw[int(k)]
            else:raw=raw[k]
        except (KeyError,IndexError,TypeError):raise ContractError("SOURCE_POINTER_UNRESOLVED")
    return raw
def uniq(a):return list(dict.fromkeys(a))
def lookup(idx,r,k=None):
    require(isinstance(r,str) and r in idx,"UNRESOLVED_REF")
    o=idx[r]
    if k:require(o["kind"] in ((k,) if isinstance(k,str) else k),"REF_KIND_MISMATCH")
    return o
def deps(o,refs):
    require(set(refs)<=set(o["dependency_refs"]),"REQUIRED_DEPENDENCY_MISSING")
def prov(o,refs):
    require(set(refs)<=set(o["provenance_refs"]),"REQUIRED_PROVENANCE_MISSING")
def legacy_ns(idx,o):
    if o["kind"]=="SourceArtifact":return o["payload"]["namespace"]
    if o["kind"]=="NativeRecord":n=o
    else:n=lookup(idx,o["payload"]["native_ref"],"NativeRecord")
    return lookup(idx,n["payload"]["artifact_ref"],"SourceArtifact")["payload"]["namespace"]
def bound(o,k):return o["payload"]["bindings"][k]["raw_value"]

# Distinguish physical dimension and declared analyte-equivalent quantity kind.
# Full normalized expressions only; unknown is None, never an equal category.
@lru_cache(maxsize=1024)
def unit_kind(unit,label=""):
    if not isinstance(unit,str):return None
    s=unicodedata.normalize("NFKC",unit).casefold().replace("μ","u").replace("µ","u").strip()
    s=re.sub(r"\s+"," ",s)
    table={"g":"MASS","mg":"MASS","ug":"MASS","mcg":"MASS","kg":"MASS",
           "kcal":"ENERGY","kj":"ENERGY","iu":"IU","ug rae":"RAE","mcg rae":"RAE","ug_rae":"RAE","mcg_rae":"RAE",
           "ug re":"RE","mcg re":"RE","ug_re":"RE","mcg_re":"RE",
           "mg α-te":"ALPHA_TE","mg αte":"ALPHA_TE","mg ate":"ALPHA_TE","mg_ate":"ALPHA_TE","mg alpha-te":"ALPHA_TE",
           "ug dfe":"DFE","mcg dfe":"DFE","ug_dfe":"DFE","mcg_dfe":"DFE","ml":"VOLUME","l":"VOLUME"}
    if label=="GI" and s in ("","gi"):return "DIMENSIONLESS_GI"
    return table.get(s)
def unit_relation(a,b):
    if a is None or b is None:return "UNRESOLVED"
    return "SAME_DECLARED_QUANTITY_KIND" if a==b else "DIFFERENT_QUANTITY_KIND"
def component_prior(policy,name,unit):
    return policy["component_prior"].get(name,{}).get(unit_kind(unit,name))
def component_kinds(policy,source,target):
    a=unit_kind(source["native_unit"],source["native_name"])
    b=policy["fdc_quantity_kind_overrides"].get(target["native_id"],unit_kind(target["native_unit"],target["native_name"]))
    return a,b,unit_relation(a,b)
def compatible_basis(from_basis,to_basis,from_state,to_state,density=None,serving_mass=None):
    require(from_state==to_state and from_state not in ("UNKNOWN","PENDING",None),"FOOD_STATE_UNQUALIFIED")
    require(from_basis not in ("UNKNOWN","PENDING",None) and to_basis not in ("UNKNOWN","PENDING",None),"MEASUREMENT_BASIS_UNQUALIFIED")
    if from_basis==to_basis:return
    if {from_basis,to_basis}=={"PER_100G","PER_100ML"}:
        require(number(density) is not None and number(density)>0,"DENSITY_REQUIRED")
    elif {from_basis,to_basis}=={"PER_SERVING","PER_100G"}:
        require(number(serving_mass) is not None and number(serving_mass)>0,"PORTION_MASS_REQUIRED")
    else:raise ContractError("BASIS_CONVERSION_UNAUTHORIZED")
def exact_component_guard(source_kind,target_kind):
    require(unit_relation(source_kind,target_kind)=="SAME_DECLARED_QUANTITY_KIND","COMPONENT_QUANTITY_KIND_UNQUALIFIED")
    return "QUANTITY_KIND_ONLY_NOT_ANALYTICAL_EQUIVALENCE"

# OFF schema field definition and actual product-level label semantics are separate.
# Market/country tags alone never establish analyte or label transformation.
OFF_DECLARED={"carbohydrates":"cc:CARBOHYDRATE_AVAILABLE","carbohydrates-total":"cc:CARBOHYDRATE_TOTAL"}
def off_semantics(field):
    return {"declared_component_ref":OFF_DECLARED[field],
            "effective_component_ref":"cc:CARBOHYDRATE_UNSPECIFIED",
            "record_definition_status":"PENDING_ORIGINAL_LABEL_AND_TRANSFORMATION",
            "measurement_equivalence":"NOT_QUALIFIED"}
def off_basis(row):
    b=row.get("nutrition_data_per")
    return {"100g":"SOURCE_DECLARED_100G","100ml":"SOURCE_DECLARED_100ML","serving":"SOURCE_DECLARED_SERVING"}.get(b,"SOURCE_BASIS_UNRESOLVED")
def off_extract(row,source_hash,locator):
    n=row.get("nutriments")
    if not isinstance(n,dict):return []
    out=[]
    for k in OFF_DECLARED:
        a=k+"_100g"
        if a not in n:continue
        s=off_semantics(k)
        out.append({"snapshot_sha256":source_hash,"source_locator":locator,"native_field":a,
                    "declared_component_ref":s["declared_component_ref"],"effective_component_ref":s["effective_component_ref"],
                    "source_raw":copy.deepcopy(n[a]),"numerator_unit":"SOURCE_SCHEMA_G_CANDIDATE_NOT_ROW_QUALIFIED",
                    "basis_declaration":off_basis(row),"record_definition_status":s["record_definition_status"],"qualification":"HOLD"})
    return out

@lru_cache(maxsize=60000)
def qualifiers(label):
    s=unicodedata.normalize("NFKC",str(label)).casefold()
    e=set()
    def word(t):return re.search(r"(?<![a-z])"+re.escape(t)+r"(?![a-z])",s) is not None
    groups={"raw":("raw","uncooked"),"cooked":("cooked","boiled","steamed","braised","roasted","baked","fried","grilled","stewed","poached"),
            "fried":("fried","deep fried"),"frozen":("frozen",),"fresh":("fresh",),"dried":("dried","dehydrated"),
            "sweetened":("sweetened","added sugar"),"unsweetened":("unsweetened","no added sugar","sugar free"),
            "salted":("salted",),"unsalted":("unsalted","no added salt"),"peeled":("peeled","skinless"),"unpeeled":("unpeeled","with skin")}
    for k,v in groups.items():
        if any(word(t) for t in v):e.add(k)
    # Explicit Chinese cooking/state terms, not bare substring 生 or 干 everywhere.
    if re.search(r"\(生\)$",s) or re.match(r"^生(?:鸡|鸭|猪|牛|羊|鱼|虾|蟹|肉|蛋|米|面|食材)",s):e.add("raw")
    if re.search(r"\(熟\)$",s) or re.match(r"^熟(?:鸡|鸭|猪|牛|羊|鱼|虾|蟹|肉|蛋|米|面)",s):e.add("cooked")
    if any(v in s for v in ("红烧","清蒸","蒸","水煮","煮","炖","卤","焖","烤","煎","炸","炒","焯","熟制")):e.add("cooked")
    if any(v in s for v in ("油炸","炸","炒")):e.add("fried")
    if any(v in s for v in ("冷冻","冰冻")) or re.match(r"^冻(?:鱼|虾|肉|鸡|牛|猪|羊)",s):e.add("frozen")
    if "新鲜" in s or re.match(r"^鲜(?:鱼|虾|肉|奶|果|蔬)",s):e.add("fresh")
    if any(v in s for v in ("脱水","干制")) or re.search(r"\(干\)$",s):e.add("dried")
    for k,v in (("sweetened","加糖"),("unsweetened","无糖"),("salted","加盐"),("unsalted","无盐"),("peeled","去皮"),("unpeeled","带皮")):
        if v in s:e.add(k)
    return frozenset(e)
def conflicts(a,b):
    l=qualifiers(a);r=qualifiers(b)
    return sorted(x+"<>"+y for x,y in (("raw","cooked"),("raw","fried"),("fresh","frozen"),("fresh","dried"),("sweetened","unsweetened"),("salted","unsalted"),("peeled","unpeeled"))
                  if (x in l and y in r) or (y in l and x in r))
def namespace_domain(policy,ns):
    for r in policy["rights_rules"]:
        if ns.startswith(r["prefix"]):return r["domain"]
    return policy["default_rights_domain"]
def expected_family(policy,scope,label):
    if scope=="nutridata:ingredient":
        if label.startswith("《中国食物成分表》"):return "CHINA_FOOD_COMPOSITION_TABLE"
        return policy["nutridata_family_exact"].get(label,"COMMERCIAL_OR_ORGANIZATION_DECLARED")
    return policy["family_by_namespace"].get(scope)
def independence_guard(families):
    require(bool(families),"SOURCE_FAMILY_MISSING")
    # Existing source-family declarations are explicitly not independent measurement evidence.
    require(all(f["independence_status"]=="INDEPENDENCE_VERIFIED_FOR_TASK" and f["independent_measurement_claim"] is True for f in families),"INDEPENDENCE_NOT_QUALIFIED")
    require(len({f["potential_family"] for f in families})==len(families),"DEPENDENT_SOURCE_FAMILY")
def link_policy(policy,lns,rns,lk,rk,key_path=""):
    cand=[r for r in policy["link_rules"] if (r["left_namespace"],r["right_namespace"],r["left_kind"],r["right_kind"])==(lns,rns,lk,rk)
          and (not r.get("binding_suffix") or key_path.endswith(r["binding_suffix"]))]
    require(len(cand)==1,"SOURCE_LINK_POLICY_UNREGISTERED")
    return cand[0]
def key_transform(a,b,rule):
    if rule=="EXACT_TEXT":require(str(a)==str(b),"NATIVE_KEY_MISMATCH")
    elif rule=="INGR_PAD_10":require(str(b).isdigit() and str(a)=="ingr_"+str(b).zfill(10),"NATIVE_KEY_MISMATCH")
    else:raise ContractError("KEY_TRANSFORM_UNREGISTERED")
def recipe_policy(policy,source,parent=None):
    cand=[r for r in policy["recipe_rules"] if r["source_namespace"]==source and (parent is None or r["parent_namespace"]==parent)]
    require(len(cand)==1,"RECIPE_POLICY_UNREGISTERED");return cand[0]
def quality_status(delta,threshold):
    return "HOLD_SOURCE_TOTAL_CONFLICT" if abs(delta)>threshold else "WITHIN_EXPLORATORY_TOLERANCE_NOT_QUALIFIED"
class Schemas:
    def __init__(self,path):
        self.schema=load(path);Draft202012Validator.check_schema(self.schema)
        self.defs=self.schema["$defs"];self.kinds={x["$ref"].split("/")[-1] for x in self.schema["oneOf"]}
        # Dispatch by kind, not evaluating 42 oneOf branches for every record.
        self.validators={k:Draft202012Validator({"$schema":self.schema["$schema"],"$defs":self.defs,"$ref":"#/$defs/"+k},format_checker=FormatChecker()) for k in self.kinds}
    def validate(self,o):
        require(o.get("kind") in self.validators,"UNREGISTERED_KIND")
        e=next(self.validators[o["kind"]].iter_errors(o),None)
        if e is not None:
            # Avoid emitting raw cell values; only schema path/keyword.
            raise ContractError("SCHEMA_"+str(e.validator)+":"+"/".join(map(str,e.absolute_path)))
        revision_ok(o)
