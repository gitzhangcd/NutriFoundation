#!/usr/bin/env python3
"""R2-P2 initial bounded source-only sparse + frozen dense hybrid experiment.
No new embedding inference; no critic IDs in query generation; no scientific release.
Separate candidate generation and post-freeze development scoring."""
import argparse, math, re, sys, unicodedata, os, json
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"u3r2"))
from compare_reference import (parse_standards, Standards, key, read, lines, put, putl, sha, dg, require, peel_conflict, SCOPES, EXT, KS)
BASE=Path("runs/B2/U3-B/C2/R2")
P1=BASE/"P1/real_001"
R2=BASE/"real_001"
PROFILE="UDF-R2-P2-DEV-0.2-DETERMINISTIC"
# Component-level bilingual hypotheses authored from source-only development
# terminology; never accepted ontology aliases. No target identity or ID rules.
LEX={}
PAT=None
def set_lexicon(lex):
 global LEX,PAT
 require(isinstance(lex,dict) and bool(lex) and all(isinstance(k,str) and k and isinstance(v,str) and v for k,v in lex.items()),"LEXICON_SCHEMA")
 LEX=dict(lex)
 PAT=re.compile("|".join(map(re.escape,sorted(LEX,key=lambda x:(-len(x),x)))))
# Strong source terms, optional qualifiers and composition components are kept apart.
FORMS={"roasted","baked","braised","fried","dried","cooked","raw","skin","peeled","crispy","sauce","pan","stir","dry","pot","representative","value","ketogenic","glucono","delta","lactone"}
STOP={"a","an","the","with","of","and","or","in","for","to","from","on","as","is","food","product","made","not","other"}
def toks(s):
 s=unicodedata.normalize("NFKC",str(s)).lower()
 w=re.findall(r"[a-z]+",s)
 out=[]
 for t in w:
  if t in STOP:continue
  if t.endswith("ies") and len(t)>4:t=t[:-3]+"y"
  elif t.endswith("s") and not t.endswith(("ss","us","is")) and len(t)>3:t=t[:-1]
  out.append(t)
 return set(out)
def segments(s):
 require(PAT is not None,"LEXICON_REQUIRED")
 return [{"source_span":m.group(),"start":m.start(),"end":m.end(),"english_hypothesis":LEX[m.group()]} for m in PAT.finditer(s)]
def query(row):
 label=row["source_native_label"]
 alias=[x["text"] for x in row.get("native_aliases",[]) if isinstance(x,dict) and isinstance(x.get("text"),str)]
 ingredients=row.get("reference_recipe_ingredient_names",[])
 main=segments(label); terms=set().union(*(toks(x["english_hypothesis"]) for x in main))
 identity=terms-FORMS
 # Aliases kept as hypotheses; they cannot add verified source identity.
 alias_terms=set().union(*(toks(x["english_hypothesis"]) for a in alias for x in segments(a)))
 components=[{"source_ingredient":a,"hypotheses":segments(a)} for a in ingredients]
 cterms=[set().union(*(toks(x["english_hypothesis"]) for x in a["hypotheses"]))-FORMS for a in components]
 residue=PAT.sub("",label)
 return {"source_label":label,"source_ref":row["source_ref"],"review_id":row["review_id"],"source_kind":row["native_kind"],
  "source_locator":row["source_locator"],"source_anchor_ref":row["source_anchor_ref"],"artifact_sha256":row["artifact_sha256"],
  "label_hypotheses":main,"native_alias_raw":alias,"alias_hypotheses":[segments(a) for a in alias],
  "reference_recipe_components":components,"context_locator":row.get("context_locator"),
  "identity_tokens":sorted(identity),"qualifier_tokens":sorted(terms&FORMS),"alias_tokens":sorted(alias_terms),
  "component_tokens":[sorted(x) for x in cterms if x],"untranslated_label_residual":residue,
  "uncertainties":["SPECIES_EDIBLE_PART_PROCESS_COMPOSITION_NOT_INFERRED_FROM_MATCH","NATIVE_ALIAS_NOT_VERIFIED_EQUIVALENCE","REFERENCE_RECIPE_NOT_PHYSICAL_COMPOSITION"],
  "translation_status":"DEVELOPMENT_HYPOTHESIS","mapping_release":"HOLD"}
def weighted_match(q,t,idf):
 if not q or not t:return 0.0
 inter=q&t
 return math.fsum(idf.get(w,1.0) for w in sorted(inter))/math.fsum(idf.get(w,1.0) for w in sorted(q)) * (0.72+0.28*len(inter)/max(1,len(t)))
def score(q,doc,idf):
 ident=set(q["identity_tokens"]); quals=set(q["qualifier_tokens"])
 alias=set(q["alias_tokens"])-FORMS
 full=ident|quals
 comp=[set(x) for x in q["component_tokens"]]
 def surface(t):
  return max(0.65*weighted_match(ident,t,idf)+0.35*weighted_match(full,t,idf),
    0.72*weighted_match(alias,t,idf),0.62*max([weighted_match(x,t,idf) for x in comp] or [0]))
 lab=surface(doc["label"])
 alt=max([surface(a) for a in doc["aliases"]] or [0])
 definition=surface(doc["definition"])
 return max(lab,0.90*alt,0.62*definition), (lab,alt,definition)
def route(q,t,old):
 if old and (old["prior_red"] or old["explicit_conflicts"] or old["proposal_route"].startswith("HOLD")):return "HOLD_INHERITED_R1"
 if peel_conflict(q["source_label"],t["native_label"]):return "HOLD_EXPLICIT_PEELED_UNPEELED"
 return "QUESTION_ONLY_R1_REVALIDATION_REQUIRED" if old else "HOLD_NEW_EDGE_R1_NOT_RUN"
def target_docs(root,universe,vocab):
 out=defaultdict(list)
 for scope,keys in universe.items():
  for k in sorted(keys):
   v=vocab[key(k[0],k[2])]
   require(not v["deprecated"],"DEPRECATED_TARGET")
   out[scope].append({"key":k,"native_label":v["label"],"locator":v["locator"],
       "label":toks(v["label"]),"aliases":[toks(a) for a in v["aliases"]],"definition":toks(" ".join(v["definitions"]))})
 return out
def idfs(docs):
 df=Counter()
 for x in docs:df.update(x["label"]|x["definition"]|set().union(*x["aliases"]))
 return {w:1+math.log((len(docs)+1)/(n+1)) for w,n in df.items()}
def fused_rank(sparse,old,budget):
 # Same original pre-ranking pool budget; sparse top20 + existing dense ranks.
 # Lexical expansion is primary; existing dense order acts as secondary support.
 sr={x:i+1 for i,x in enumerate(sparse[:20])}
 lr={tuple(x["target_key"]):x["label_rank"] for x in old if x["label_rank"]}
 cr={tuple(x["target_key"]):x["context_rank"] for x in old if x["context_rank"]}
 def rrf(k):return 2/(60+sr[k]) if k in sr else 0
 def score_(k):return rrf(k)+(1/(60+lr[k]) if k in lr else 0)+(1/(60+cr[k]) if k in cr else 0)
 return sorted(set(sr)|set(lr)|set(cr),key=lambda k:(-score_(k),k))[:budget]
def fence(root):
 manifest=read(root/P1/"private/InputFence.json")
 require(len(manifest)==127,"P1_INPUT_COUNT")
 p1=root/P1/"P1FreezeReceipt.json"
 require(sha(p1)=="4f8a6402bc4a34e5e1058670c735bbf78aabef26c949b3e6dc6a53c9fc630ae5","P1_RECEIPT_PIN")
 receipt=read(p1);require(receipt["reserved32_outcomes_read"]==0 and receipt["mapping_release_authorized"] is False,"P1_RELEASE")
 for rel,h in receipt["output_file_hashes"].items():manifest[str(P1/rel)]=h
 manifest[str(P1/"P1FreezeReceipt.json")]=sha(p1)
 require(all(sha(root/p)==h for p,h in manifest.items()),"FROZEN_INPUT_DRIFT")
 return manifest
def generate(root,out,lexicon,lexicon_sha):
 require(not out.exists() and out.is_relative_to(root/BASE/"P2"),"NEW_P2_RUN_REQUIRED")
 pins=fence(root)
 require(lexicon.is_relative_to(root/BASE/"P2/private") and not lexicon.is_symlink() and sha(lexicon)==lexicon_sha,"PRIVATE_LEXICON_PIN")
 pins[str(lexicon.relative_to(root))]=lexicon_sha
 set_lexicon(read(lexicon))
 # Project only selection metadata from authorized P1 first44 comparison;
 # reserved32 projection/outcomes never parsed.
 ids={r["review_id"] for r in lines(root/P1/"private/ReferenceComparisonRecords.jsonl") if r["current_model_query"]}
 require(len(ids)==19,"DEV19")
 source=[x for x in read(root/R2/"reviewer_source_only/R2Review44.json") if x["review_id"] in ids]
 require(len(source)==19 and len({x["source_ref"] for x in source})==19,"DEV_SOURCE")
 query_rows=[query(x) for x in source];refs={x["source_ref"] for x in query_rows}
 # Same frozen universes; no expansion outside them.
 un=read(root/R2/"controller_private/FrozenTargetUniverse.json")
 by=defaultdict(set)
 for k in un["original"]:by[k[0]].add(tuple(k))
 by["FOODON_EXTENSION"]={tuple(k) for k in un["extension"]}
 require(sum(len(v) for k,v in by.items() if k!="FOODON_EXTENSION")==28845 and len(by["FOODON_EXTENSION"])==1174,"UNIVERSE")
 vocab,_=parse_standards(Standards(root));docs=target_docs(root,by,vocab)
 idx={s:{d["key"]:d for d in ds} for s,ds in docs.items()}
 weights={s:idfs(ds) for s,ds in docs.items()}
 pools=defaultdict(list)
 for m in read(root/R2/"controller_private/ProposalManifest.json").values():
  f=root/R2/m["file"];require(sha(f)==m["sha256"],"POOL_PARTITION_HASH");pins[str(f.relative_to(root))]=m["sha256"]
  for x in lines(f):
   if x["source_legacy_ref"] not in refs:continue
   k=tuple(x["target_key"]);sc="FOODON_EXTENSION" if x["target_scope"]==EXT else k[0]
   pools[(x["source_legacy_ref"],sc)].append(x)
 require(len(pools)==19*4,"BASELINE_POOL_GROUPS")
 outrows=[];rankrows=[]
 for q in query_rows:
  for sc,ds in docs.items():
   old=pools[(q["source_ref"],sc)];oi={tuple(x["target_key"]):x for x in old};budget=len(oi)
   require(budget==len(old) and set(oi)<=set(idx[sc]),"BASELINE_POOL_IDENTITY")
   ranked=[]
   for d in ds:
    val,channels=score(q,d,weights[sc])
    if val>0:ranked.append((d["key"],val,channels))
   ranked.sort(key=lambda x:(-x[1],x[0]));sparse=[x[0] for x in ranked]
   scs={k:(v,ch) for k,v,ch in ranked}
   # use identical per-case/scope retained budget, not an expanded denominator
   base=sorted(oi,key=lambda k:(oi[k]["frozen_pool_rank"] or 99999,-oi[k]["fusion_score"],k)) if sc!="FOODON_EXTENSION" else sorted(oi,key=lambda k:(-oi[k]["fusion_score"],k))
   lists={"BASELINE_FUSION":base,"SOURCE_SPARSE":sparse[:budget],"HYBRID":fused_rank(sparse,old,budget)}
   for arm,keys in lists.items():
    require(len(keys)<=budget and len(set(keys))==len(keys),"POOL_BUDGET")
    rankrows.append({"review_id":q["review_id"],"scope":sc,"arm":arm,"pool_budget":budget,"targets":[list(k) for k in keys]})
    for i,k in enumerate(keys,1):
     d=idx[sc][k];v,ch=scs.get(k,(0,(0,0,0)))
     outrows.append({"review_id":q["review_id"],"scope":sc,"arm":arm,"rank":i,"target_key":list(k),"target_locator":d["locator"],
      "target_native_label":d["native_label"],"query_digest":dg(q),"sparse_score":v,"channel_scores":list(ch),
      "candidate_role":"COMPOSITION_OR_DISH_REVIEW" if q["source_kind"]=="RECIPE_REFERENCE" else "FOOD_IDENTITY_REVIEW",
      "route":route(q,d,oi.get(k)),"candidate_relation":"UNRESOLVED","accepted_equivalence":False,
      "development_concept_review_authorized":False,"measurement_transfer":"HOLD","mapping_release":"HOLD"})
 require(all(sha(root/p)==h for p,h in pins.items()),"FENCE_CHANGED")
 out.mkdir(parents=True,mode=0o700);priv=out/"private";priv.mkdir(mode=0o700)
 putl(priv/"QueryHypotheses.jsonl",query_rows);putl(priv/"CandidateQuestions.jsonl",outrows);putl(priv/"Ranks.jsonl",rankrows)
 put(out/"CandidateFreeze.json",{"profile":PROFILE,"method_sha256":sha(Path(__file__)),"query_count":19,"groups":len(rankrows),"candidate_rows":len(outrows),"input_fences":pins,
  "private_hashes":{p.name:sha(p) for p in priv.iterdir()},"reserved32_semantics_read":False,"mapping_release":False,"method_status":"INITIAL_DEVELOPMENT_VARIANT_NOT_FINAL_FREEZE"})
def evaluate(root,out):
 fr=read(out/"CandidateFreeze.json");require(fr["method_sha256"]==sha(Path(__file__)),"METHOD_DRIFT")
 require(all(sha(root/p)==h for p,h in fr["input_fences"].items()),"INPUT_DRIFT")
 require(all(sha(out/"private"/p)==h for p,h in fr["private_hashes"].items()),"CANDIDATE_DRIFT")
 ranks=list(lines(out/"private/Ranks.jsonl"));ids={x["review_id"] for x in ranks};require(len(ids)==19,"DEV19")
 # Critic reference candidates accessed only at development scoring phase.
 cfg=read(root/"configs/audit/tasks/B2_U3R2_REF44_Gemini_001.json")
 rec={x["review_id"]:x for x in lines(root/cfg["output"]["directory"]/"ReviewRecords.jsonl") if x["review_id"] in ids}
 require(set(rec)==ids,"REFERENCE_ID")
 pos=defaultdict(set);neg=defaultdict(set)
 for r in lines(root/P1/"private/ReferenceGapAttribution.jsonl"):
  if r["review_id"] in ids and r["domain"]=="ORIGINAL":pos[r["review_id"]].add(tuple(r["target_key"]))
 for rid,x in rec.items():neg[rid]={tuple(t["target_key"]) for t in x["hard_negatives"]}
 require(sum(map(len,pos.values()))==43 and len(pos)==18,"REFERENCE_DENOMINATOR")
 agg=[]
 for arm in ("BASELINE_FUSION","SOURCE_SPARSE","HYBRID"):
  for k in [1,3,5,12,"POOL"]:
   cand=defaultdict(set)
   for r in ranks:
    if r["arm"]!=arm or r["scope"]=="FOODON_EXTENSION":continue
    cand[r["review_id"]].update(tuple(t) for t in (r["targets"] if k=="POOL" else r["targets"][:k]))
   require(set(cand)==ids,"CANDIDATE_CASES")
   agg.append({"arm":arm,"k_per_scope":k,"cases":19,"reference_cases":18,
    "reference_hit_cases":sum(bool(cand[i]&pos[i]) for i in ids),"reference_edges_hit":sum(len(cand[i]&pos[i]) for i in ids),
    "reference_edges":43,"candidate_edges":sum(map(len,cand.values())),
    "critic_negative_overlap":sum(len(cand[i]&neg[i]) for i in ids),
    "unjudged_edges":sum(len(cand[i]-pos[i]-neg[i]) for i in ids)})
 require(next(x for x in agg if x["arm"]=="BASELINE_FUSION" and x["k_per_scope"]=="POOL")["reference_edges_hit"]==4,"BASELINE_POOL_REPLAY")
 require(next(x for x in agg if x["arm"]=="BASELINE_FUSION" and x["k_per_scope"]==12)["reference_hit_cases"]==3,"BASELINE_TOP12_REPLAY")
 candidates=list(lines(out/"private/CandidateQuestions.jsonl"))
 require(all(not x["accepted_equivalence"] and not x["development_concept_review_authorized"] and x["mapping_release"]=="HOLD" for x in candidates),"RELEASE")
 report={"status":"INITIAL_DEVELOPMENT_COMPARISON_ONLY","method_sha256":fr["method_sha256"],"candidate_freeze_sha256":sha(out/"CandidateFreeze.json"),
 "metrics":agg,"route_counts":dict(Counter(x["route"] for x in candidates)),"scientific_precision_recall":"NOT_ESTIMABLE",
 "reserved32_outcomes_read":0,"expert_gold":0,"mapping_releases":0,
 "limitations":["19 development exposed cases; not independent validation","component lexicon author-generated from source terms; no new dense embeddings","new edge requires full R1 revalidation; no formal conditional mapping","all raw query and candidate rows local only"]}
 put(out/"P2DevelopmentReport.json",report)
 print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("phase",choices=["generate","evaluate"]);a.add_argument("--root",type=Path,default=Path("."));a.add_argument("--out",type=Path,required=True);a.add_argument("--lexicon",type=Path);a.add_argument("--lexicon-sha");z=a.parse_args()
 if z.phase=="generate":
  require(z.lexicon is not None and z.lexicon_sha is not None,"PRIVATE_LEXICON_REQUIRED")
  generate(z.root.resolve(),z.out.resolve(),z.lexicon.resolve(),z.lexicon_sha)
 else:evaluate(z.root.resolve(),z.out.resolve())
