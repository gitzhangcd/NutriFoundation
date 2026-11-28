#!/usr/bin/env python3
"""A2.8 local source-only projection and query freeze. No reference/rank outcome input."""
import sys,json,hashlib,os,collections
from pathlib import Path
from a28_query import reconstruct,need,FIELDS
B=Path("runs/B2/U3-B/C2/R2/P2/A2");P=B.parent
OUT=B/"query_reconstruction_001";PACK=B/"query_source_projection_001"
SCOPES=("FoodOn","FDC_SR_Legacy","FNDDS","FOODON_EXTENSION")
PINS={}
def sha(b):return hashlib.sha256(b).hexdigest()
def snap(p,h):
 p=Path(p);need(not p.is_absolute() and ".." not in p.parts and p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(Path.cwd().resolve()),"INPUT_PATH")
 b=p.read_bytes();need(sha(b)==h,"PIN_DRIFT:"+str(p));PINS[str(p)]=h;return b
def j(p,h):return json.loads(snap(p,h))
def canon(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def save(p,x):
 b=x if isinstance(x,bytes) else canon(x)
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,"wb") as f:f.write(b);f.flush();os.fsync(f.fileno())
 return sha(b)
def project():
 need(not PACK.exists(),"OUTPUT_EXISTS")
 p19=j(P/"A1/projection_001/RetrievalInput19.json","8890a82349033436deab6b3bff6f736956fec739797b5576ab96d6ea36c2d729")
 prep=j(B/"local_001/PreparationFreeze.json","38b36cd2e44d5c538ad8a18bf560229532cf06e46dc58a36c870c4b9ac1be1f4")
 p32=j(B/"local_001/controller_private/RetrievalInput32.json",prep["retrieval_packet_sha256"])
 staged=j(B/"local_001/reviewer_staging/runs/B2/U3-B/C2/R2/real_001/reserved_source_only/R2Calibration32.json","c8a65e45fe8ae4b2435ff5296889441fbe56f672ea1890a611f9d2057eae6a4a")
 need(p32["source_records"]==staged,"SOURCE32_DRIFT")
 # Read only source-context partition and project selected 51, never review outputs.
 hist=[json.loads(x)["payload"] for x in snap("runs/B2/U3-B/real_001/private/typed_partitions/MIXED_RESTRICTED_f05fbb56a95c4498/QueryContextRecord.jsonl","767fd07e254d12c64e131c6144a971d5ef34560ee40934eccb4a6f06c252a2dd").splitlines()]
 ix={x["source_legacy_ref"]:x for x in hist};need(len(ix)==len(hist)==284,"HIST_CLOSURE")
 rows=[];budgets=[]
 for cohort,p,n,hcount in [("EXPOSED19",p19,19,2427),("EXPOSED32",p32,32,3875)]:
  need(set(p)=={"purpose","source_records","dense_rank_hints","reviewer_results_included","mapping_release"} and p["reviewer_results_included"] is False and p["mapping_release"] is False and len(p["source_records"])==n and len(p["dense_rank_hints"])==hcount,"PACKET")
  ids={s["review_id"] for s in p["source_records"]};need(len(ids)==n,"CASE_IDS")
  # Only aggregate budgets from hints. No hint target identity is exported.
  counts=collections.Counter((x["review_id"],x["scope"]) for x in p["dense_rank_hints"])
  need(set(counts)=={(i,s) for i in ids for s in SCOPES},"CAP_CLOSURE")
  for s in p["source_records"]:
   need(set(s)==FIELDS and s["status"]=="NOT_REVIEWED","SOURCE_FIELDS")
   h=ix[s["source_ref"]]
   need(h["native_label"]==s["source_native_label"] and h["native_alias_raw"]==[a["text"] for a in s["native_aliases"]] and h["native_ingredient_names"]==s["reference_recipe_ingredient_names"][:5] and h["artifact_sha256"]==s["artifact_sha256"],"HIST_SOURCE_BINDING")
   rows.append({"cohort":cohort,"source":s,"context":{k:h[k] for k in ("label_query","context_query","state_tokens")}})
   budgets.extend({"review_id":s["review_id"],"scope":sc,"pool_budget":counts[s["review_id"],sc]} for sc in SCOPES)
 need(len({r["source"]["source_ref"] for r in rows})==len({r["source"]["review_id"] for r in rows})==51 and len(budgets)==204,"CLOSURE")
 PACK.mkdir(mode=0o700)
 h=save(PACK/"PrivateSourceOnly51.json",{"version":"A2.8-SOURCE-ONLY-PROJECTION-v0.1","rows":rows,"budgets":budgets,"reference_outputs_included":False,"rank_hints_included":False,"mapping_release":False})
 r={"status":"PASS_SOURCE_ONLY_PROJECTION","cases":51,"cohorts":{"EXPOSED19":19,"EXPOSED32":32},"scope_budgets":204,"hint_rows_counted":6302,"source_only_packet_sha256":h,"input_sha256":PINS,"target_ids_projected":0,"reference_outputs_read":0,"mapping_release":0}
 print(json.dumps({"receipt_sha256":save(PACK/"ProjectionReceipt.json",r),"packet_sha256":h,"cases":51,"budgets":204}))
def queries(receipt_sha):
 need(not OUT.exists(),"OUTPUT_EXISTS")
 r=j(PACK/"ProjectionReceipt.json",receipt_sha)
 need(r["status"]=="PASS_SOURCE_ONLY_PROJECTION","PROJECTION")
 p=j(PACK/"PrivateSourceOnly51.json",r["source_only_packet_sha256"])
 need(set(p)=={"version","rows","budgets","reference_outputs_included","rank_hints_included","mapping_release"} and not any(p[k] for k in ("reference_outputs_included","rank_hints_included","mapping_release")),"PROJECTION_SCOPE")
 lex=j(P/"private/DevelopmentLexicon_v0.1.json","846b8baa30a8bd1782cf93876163bdd37d625e169497fe77b007df240804b778")
 need(len(lex)==72,"LEXICON")
 rows=[];stats=collections.defaultdict(collections.Counter)
 for item in p["rows"]:
  need(set(item)=={"cohort","source","context"},"PROJECTION_ROW")
  q=reconstruct(item["source"],item["context"],lex);q["cohort"]=item["cohort"];rows.append(q)
  z=stats[item["cohort"]];z["cases"]+=1;z["native_label_retained_in_both_new_views"]+=all(x.startswith("query: "+q["native_label"]) for x in q["q1"]);z["source_kind_bound"]+=bool(q["identity_role"]);z["label_hypothesis_nonempty"]+=any(h["field"]=="source_native_label" for h in q["hypotheses"]);z["hypothesis_spans"]+=len(q["hypotheses"]);z["state_mentions_nonempty"]+=bool(q["state_mentions"]);z["alias_nonempty"]+=bool(q["native_aliases"]);z["recipe_context_nonempty"]+=bool(q["reference_recipe_ingredients"])
 need(len(rows)==51 and len(p["budgets"])==204,"QUERY_CLOSURE")
 OUT.mkdir(mode=0o700)
 a=save(OUT/"PrivateQueryViews51.json",{"version":"A2.8-QUERY-FREEZE-v0.1","queries":rows,"budgets":p["budgets"],"mapping_release":False})
 rr={"status":"PASS_SOURCE_GROUNDED_QUERY_FREEZE","source_projection_receipt_sha256":receipt_sha,"private_query_views_sha256":a,"query_module_sha256":sha(Path("src/u3r2p2a2/a28_query.py").read_bytes()),"query_controller_sha256":sha(Path(__file__).read_bytes()),"input_sha256":PINS,"counts":dict(stats),"query_cases":51,"views_per_condition":2,"no_generative_llm":True,"reference_outputs_read":0,"target_standard_payloads_read":0,"mapping_release":0}
 print(json.dumps({"receipt_sha256":save(OUT/"QueryFreezeReceipt.json",rr),"query_views_sha256":a,"counts":dict(stats)},ensure_ascii=False))
if __name__=="__main__":
 if sys.argv[1:]==["project"]:project()
 elif len(sys.argv)==3 and sys.argv[1]=="queries":queries(sys.argv[2])
 else:raise SystemExit("project or queries RECEIPT_SHA")
