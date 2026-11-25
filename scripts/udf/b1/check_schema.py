#!/usr/bin/env python3
"""Check the exact JSON-Schema keyword subset used by this B1 catalog.
Not a general JSON Schema implementation. Runtime contract.py remains authoritative.
"""
import argparse,json,re,pathlib as P
from datetime import datetime
from contract import PAYLOAD_FIELDS,SCI_KINDS,SCIENTIFIC_DELEGATED,canon,require,ContractError,validate_set,VERSION
from run_b1 import read_back,atomic_json,file_sha

class ShapeError(ValueError):pass
def check(ok,code):
    if not ok:raise ShapeError(code)
ALLOWED={"$ref","type","const","enum","not","oneOf","properties","required","additionalProperties","minProperties","minLength","pattern","format","minimum","items","uniqueItems"}
def validate(x,s,defs):
    check(set(s)<=ALLOWED,"UNSUPPORTED_SCHEMA_KEYWORD")
    if "$ref" in s:
        check(s["$ref"].startswith("#/$defs/"),"NONLOCAL_REF")
        return validate(x,defs[s["$ref"][8:]],defs)
    if "oneOf" in s:
        n=0
        for opt in s["oneOf"]:
            try:validate(x,opt,defs);n+=1
            except ShapeError:pass
        check(n==1,"ONE_OF")
    if "not" in s:
        try:validate(x,s["not"],defs)
        except ShapeError:pass
        else:raise ShapeError("NOT")
    if "const" in s:check(canon(x)==canon(s["const"]),"CONST")
    if "enum" in s:check(any(canon(x)==canon(v) for v in s["enum"]),"ENUM")
    if "type" in s:
        t=s["type"];typ={"null":x is None,"object":isinstance(x,dict),"array":isinstance(x,list),"string":isinstance(x,str),"integer":isinstance(x,int) and not isinstance(x,bool)}
        check(t in typ and typ[t],"TYPE")
    if isinstance(x,str):
        if "minLength" in s:check(len(x)>=s["minLength"],"MIN_LENGTH")
        if "pattern" in s:check(re.search(s["pattern"],x) is not None,"PATTERN")
        if s.get("format")=="date-time":
            try:check(datetime.fromisoformat(x.replace("Z","+00:00")).tzinfo is not None,"DATE_TIME")
            except ValueError:raise ShapeError("DATE_TIME")
    if isinstance(x,int) and not isinstance(x,bool) and "minimum" in s:check(x>=s["minimum"],"MINIMUM")
    if isinstance(x,list):
        if s.get("uniqueItems"):check(len({canon(y) for y in x})==len(x),"UNIQUE_ITEMS")
        if "items" in s:
            for y in x:validate(y,s["items"],defs)
    if isinstance(x,dict):
        check(set(s.get("required",[]))<=set(x),"REQUIRED")
        if "minProperties" in s:check(len(x)>=s["minProperties"],"MIN_PROPERTIES")
        ps=s.get("properties",{})
        for k,v in x.items():
            if k in ps:validate(v,ps[k],defs)
            elif s.get("additionalProperties") is False:raise ShapeError("ADDITIONAL_PROPERTIES")
            elif isinstance(s.get("additionalProperties"),dict):validate(v,s["additionalProperties"],defs)

def main(schema_file,bridge_file,run,out):
    schema=json.loads(schema_file.read_text());bridge=json.loads(bridge_file.read_text())
    defs=schema["$defs"]
    actual={r["$ref"].split("/")[-1] for r in schema["oneOf"]}
    require(actual==set(PAYLOAD_FIELDS),"SCHEMA_KIND_DRIFT")
    for k,fields in PAYLOAD_FIELDS.items():
        p=defs[k]["properties"]["payload"]
        require(set(p["required"])==fields and set(p["properties"])==fields,"SCHEMA_PAYLOAD_DRIFT")
        require(defs[k]["properties"]["kind"]["const"]==k,"SCHEMA_KIND_DISCRIMINATOR")
    sc=bridge["scientific_collections"]
    require({r["kind"] for r in sc}==set(SCI_KINDS) and len({r["logical_collection"] for r in sc})==11,"SCI_COLLECTION_DRIFT")
    require({r["kind"] for r in sc if r["status"]=="DELEGATED_NDF_D0"}==set(SCIENTIFIC_DELEGATED),"SCI_DELEGATION_DRIFT")
    objs=read_back(run/"private/typed_collections")
    validate_set(objs)
    for o in objs:validate(o,defs[o["kind"]],defs)
    import copy
    # Verify rejection by schema checker, not only runtime, without raw data in report.
    m=next(x for x in objs if x["kind"]=="NutrientMeasurementDraft")
    neg=[]
    def bad(label,mut):
        x=copy.deepcopy(m);mut(x)
        try:validate(x,defs[x["kind"]],defs)
        except ShapeError as e:neg.append({"name":label,"observed":str(e),"rejected":True})
        else:neg.append({"name":label,"observed":"ACCEPT","rejected":False})
    bad("missing instance_class",lambda x:x.pop("instance_class"))
    bad("unexpected payload field",lambda x:x["payload"].update(unregistered_field=True))
    bad("pending slot with hidden value",lambda x:x["payload"].update(normalized_value={"tag":"PENDING","reason":"unknown","value":0}))
    bad("malformed immutable ref",lambda x:x["payload"].update(subject_ref="latest"))
    bad("fake release",lambda x:x.update(purpose="LOCKED_EVALUATION"))
    require(all(x["rejected"] for x in neg),"SCHEMA_NEGATIVE_FAILED")
    report={"run_id":"B1-U2A-SCHEMA-001","contract_version":VERSION,"checker":"independent stdlib check of the exact used JSON Schema keyword subset; not a general standards-conformance checker","schema_sha256":file_sha(schema_file),"bridge_sha256":file_sha(bridge_file),"schema_kind_count":len(actual),"objects_shape_validated":len(objs),"scientific_collection_declarations":len(sc),"shared_scientific_types_instantiated":2,"delegated_uninstantiated_scientific_kinds":len(SCIENTIFIC_DELEGATED),"negative_checks":neg,"negative_rejected":sum(x["rejected"] for x in neg),"status":"PASS_DRAFT_STRUCTURE_ONLY","d0_interchange_validated":False}
    atomic_json(out,report);print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--schema",type=P.Path,required=True);p.add_argument("--bridge",type=P.Path,required=True);p.add_argument("--run",type=P.Path,required=True);p.add_argument("--out",type=P.Path,required=True);a=p.parse_args();main(a.schema,a.bridge,a.run,a.out)
