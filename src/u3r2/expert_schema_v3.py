"""Create an explicitly nonactivated expert response v0.3.
Only schema contradictions repaired here. Phase-B per-edge evidence binding
and actual authority/access isolation must pass EA-P0 before any expert dispatch.
"""
import json,pathlib as P,copy,hashlib,argparse
from jsonschema import Draft202012Validator
def build(old):
 s=copy.deepcopy(old);s["$id"]="urn:nutrifoundation:udf:u3r2:expert-response:0.3";s["title"]="Expert response v0.3 (draft, dispatch HOLD)"
 s["description"]="Structural contradictions repaired. Does not implement reviewer authority, Phase-B per-edge evidence binding, or isolation. Must not be activated for expert dispatch before EA-P0."
 a,b=s["oneOf"]
 a["allOf"].append({"if":{"properties":{"initial_disposition":{"const":"HOLD_INSUFFICIENT_EVIDENCE"}}},"then":{"properties":{"independent_candidates":{"items":{"properties":{"relation":{"enum":["AMBIGUOUS","UNRESOLVED"]},"task_applicability":{"const":"UNRESOLVED"}}}}}}})
 b["properties"]["edge_judgments"]["items"]["allOf"].append({"if":{"properties":{"verdict":{"const":"REJECT_AS_EQUIVALENCE"}}},"then":{"properties":{"relation":{"not":{"const":"EXACT"}}}}})
 Draft202012Validator.check_schema(s);return s
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));x=a.parse_args();root=x.root.resolve()
 old=root/"schemas/udf/u3c2r/ExpertAdjudicationResponse_v0.2.schema.json";out=root/"schemas/udf/u3r2/ExpertAdjudicationResponse_v0.3.schema.json"
 assert hashlib.sha256(old.read_bytes()).hexdigest()=="29664e901ef85694253361699c6859ddee1bd4ecf66eb2fae8739f510c2518ae"
 s=build(json.loads(old.read_text()))
 with out.open("x",encoding="utf8") as f:json.dump(s,f,ensure_ascii=False,indent=2);f.write("\n")
 print("SCHEMA_DRAFT_CREATED",hashlib.sha256(out.read_bytes()).hexdigest())
