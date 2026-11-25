#!/usr/bin/env python3
"""Audit the frozen B2 review queue and append an independent red-route supplement.
No semantic review or mapping acceptance. No private rows in shareable report.
"""
import argparse, collections as C, hashlib, json, pathlib as P
def require(ok, code):
    if not ok: raise ValueError(code)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf8"))
def lines(p):
    with p.open(encoding="utf8") as h:
        for line in h: yield json.loads(line)
def ref(o): return o["object_id"]+"@"+o["revision_id"]
def put(p,x):
    with p.open("x",encoding="utf8") as h:json.dump(x,h,ensure_ascii=False,indent=2);h.write("\n")
def main(run,out):
    run=run.resolve();out=out.resolve()
    require(not out.exists() and not out.is_relative_to(run),"OUTPUT_MUST_BE_NEW_SIBLING")
    p=run/"private";tbl=p/"typed_collections";m=load(p/"collection_manifest.json")
    files=[p/"ReviewSourceOnlyQueue.json",p/"ReviewCandidatesHidden.json",p/"CandidateQueryRoutes.jsonl",
           tbl/"NativeVocabularyRecord.jsonl",tbl/"AlignmentRecord.jsonl",run/"B2RunReport.json",run/"ContractValidationReport.json"]
    hashes={str(q.relative_to(run)):sha(q) for q in files}
    for q in files[3:5]:require(hashes[str(q.relative_to(run))]==m[q.name]["sha256"],"COLLECTION_HASH")
    report=load(run/"B2RunReport.json");test=load(run/"ContractValidationReport.json")
    require(report["run_id"]=="B2-U3A-real_002" and test["failed"]==0,"UPSTREAM_NOT_ACCEPTED")
    native={ref(o):o["payload"] for o in lines(files[3])}
    edges={ref(o):o["payload"] for o in lines(files[4])}
    require(len(native)==report["native_vocab_records"] and len(edges)==report["alignment_candidates"],"COUNT")
    routes={r["source_ref"]:r for r in lines(files[2])}
    source=load(files[0]);hidden=load(files[1]);hid={x["review_id"]:x for x in hidden}
    require(len(source)==len(hidden)==len(hid)==40,"ORIGINAL_QUEUE")
    require({x["review_id"] for x in source}==set(hid),"QUEUE_PAIR")
    original={x["source_ref"] for x in source}
    for q in source:
        r=routes[q["source_ref"]]
        require(hid[q["review_id"]]["candidate_refs"]==r["candidate_refs"],"HIDDEN_PAIR")
        require(q["status"]=="NOT_REVIEWED" and "candidate_refs" not in q and "ranking_score" not in q,"EXPOSURE")
    reds={e["source_ref"] for e in edges.values() if e["review_route"]=="RED"}
    missed=sorted(reds-original)
    supplement=[];supp_hidden=[]
    for i,r in enumerate(missed,1):
        a=native[r];row=routes[r];rid="B2-RED-SUP-"+str(i).zfill(3)
        supplement.append({"review_id":rid,"source_ref":r,"source_scope":a["native_namespace"],"source_native_label":a["native_label"],"native_kind":a["native_kind"],
            "question":"Independently propose the concept/definition and permissible directional relation, or unresolved. Review food state and grain from source context. Do not use candidate output.","status":"NOT_REVIEWED"})
        supp_hidden.append({"review_id":rid,"candidate_refs":row["candidate_refs"]})
        require(any(edges[e]["review_route"]=="RED" for e in row["candidate_refs"]),"RED_SOURCE_MISMATCH")
    require(len(original|set(missed))==len(source)+len(supplement) and reds<=original|set(missed),"RED_COVERAGE")
    require(all(set(q)=={"review_id","source_ref","source_scope","source_native_label","native_kind","question","status"} for q in supplement),"SUPPLEMENT_ALLOWLIST")
    require(all(set(q)=={"review_id","candidate_refs"} for q in supp_hidden),"SUPPLEMENT_HIDDEN_ALLOWLIST")
    require({q["review_id"] for q in supplement}=={q["review_id"] for q in supp_hidden},"SUPPLEMENT_PAIR")
    out.mkdir(parents=True);private=out/"private";private.mkdir()
    put(private/"ReviewSourceOnlyRedSupplement.json",supplement)
    put(private/"ReviewCandidatesHiddenRedSupplement.json",supp_hidden)
    require(all(sha(run/k)==h for k,h in hashes.items()),"UPSTREAM_CHANGED")
    result={"run_id":"B2-U3A-REVIEW-QUEUE-AUDIT-001","baseline":report["run_id"],"status":"PASS_QUEUE_SUPPLEMENT_ONLY",
      "original_queue_sources":len(source),"original_unmatched_sources":sum(not hid[q["review_id"]]["candidate_refs"] for q in source),
      "rule_red_sources_total":len(reds),"original_queue_red_sources":len(reds&original),"supplement_sources":len(supplement),
      "combined_queue_sources":len(original|set(missed)),"combined_red_sources":len(reds&(original|set(missed))),
      "review_completed":0,"candidate_precision_recall":"NOT_MEASURED","mapping_release_count":0,
      "candidate_query_method_counts":dict(C.Counter(x["query_method"] for x in edges.values())),
      "max_candidates_per_query":max(x["candidate_count"] for x in routes.values()),
      "scope_limit":"Rule-red coverage is not coverage of all semantic conflicts. No independent human/critic review. Files separated locally, not a proven blind access-control system.",
      "input_hashes":{k:v for k,v in hashes.items() if k in ("B2RunReport.json","ContractValidationReport.json")},
      "upstream_files_unchanged":True,"private_outputs":["ReviewSourceOnlyRedSupplement.json","ReviewCandidatesHiddenRedSupplement.json"]}
    put(out/"ReviewQueueAudit.json",result);print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--run",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.run,x.out)
