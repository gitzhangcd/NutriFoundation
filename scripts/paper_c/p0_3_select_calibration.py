#!/usr/bin/env python3
import json, hashlib, re, urllib.request, urllib.parse, time, xml.etree.ElementTree as ET
from pathlib import Path
from ortools.sat.python import cp_model

ROOT=Path(__file__).resolve().parents[2]
UNIVERSE=ROOT/"runs/E0.4.3/P0.2.4/Gold100_Augmented_Sampling_Universe_v1.0.json"
GOLD100=ROOT/"runs/E0.4.3/P0.2.4/Gold100_Source_Set_FROZEN_v1.0.json"
OUT=ROOT/"runs/E0.4.3/P0.3"
OUT.mkdir(parents=True,exist_ok=True)

STAGE="E0.4.3-P0.3"
SOURCE_SET_SHA="fdb1189647fe4022411d3ebfd6591da2398135aed398c88ca6f85236678420ad"
SELECTION_KEY=f"{STAGE}|CALIBRATION24|{SOURCE_SET_SHA}"

def csha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

def http_get(url,retries=4):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"NutriFoundation-PaperC-P0.3/1.0"})
            with urllib.request.urlopen(req,timeout=60) as r:
                return r.read()
        except Exception as e:
            last=e
            time.sleep(min(8,1.5*(i+1)))
    raise last

def txt(node):
    if node is None: return ""
    return " ".join(" ".join(node.itertext()).split())

def pubmed_meta(pmids):
    out={}
    for i in range(0,len(pmids),80):
        ids=pmids[i:i+80]
        q=urllib.parse.urlencode({"db":"pubmed","id":",".join(ids),"retmode":"xml","tool":"NutriFoundation","email":"noreply@example.invalid"})
        root=ET.fromstring(http_get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"+q))
        for art in root.findall(".//PubmedArticle"):
            pmid=txt(art.find("./MedlineCitation/PMID"))
            if not pmid: continue
            title=txt(art.find(".//ArticleTitle"))
            abstract=" ".join(txt(x) for x in art.findall(".//Abstract/AbstractText"))
            ptypes=[txt(x) for x in art.findall(".//PublicationType") if txt(x)]
            mesh=[txt(x) for x in art.findall(".//MeshHeading/DescriptorName") if txt(x)]
            out[pmid]={"title":title,"abstract":abstract,"publication_types":ptypes,"mesh":mesh}
        time.sleep(0.35)
    return out

TITLE_NUTRI_RE=re.compile(r"\b(nutrition|nutritional|diet|dietary|food|nutrient|vitamin|mineral|calorie|selenium|iron|obesity|overweight|diabet|glyc|lipid|cholesterol|metabolic|cardiometabolic|fatty acid|malnutrition|micronutrient|macronutrient|statin)\b",re.I)
MESH_NUTRI_RE=re.compile(r"\b(nutritional|nutrition|diet|dietary|obesity|overweight|diabetes mellitus|metabolic syndrome|dyslipid|hyperlipid|cholesterol|cardiovascular diseases)\b",re.I)
VET_RE=re.compile(r"\b(canine|feline|veterinary|dog|dogs|cat|cats|murine|mouse|mice|rat|rats)\b",re.I)
PROTOCOL_RE=re.compile(r"\b(study protocol|trial protocol|protocol for a randomized|protocol for a randomised|systematic review protocol|protocol:)\b",re.I)
COMP_RE=re.compile(r"\b(secondary analysis|prespecified secondary analysis|post[- ]hoc analysis|subgroup analysis|follow[- ]up analysis)\b",re.I)
RCT_TITLE_RE=re.compile(r"\b(randomized|randomised|controlled trial|clinical trial)\b",re.I)
OBS_RE=re.compile(r"\b(cohort|case[- ]control|cross[- ]sectional|observational|prospective study|retrospective study)\b",re.I)

def semantic_classification(meta,source_record):
    title=meta.get("title") or source_record.get("title") or ""
    abstract=meta.get("abstract") or ""
    ptypes=" | ".join(meta.get("publication_types",[])).lower()
    mesh_text=" ".join(meta.get("mesh",[]))
    text=(title+" "+abstract)
    if PROTOCOL_RE.search(text) or "clinical trial protocol" in ptypes:
        return None,None,"protocol_not_evidence_result"
    if VET_RE.search(title+" "+" ".join(meta.get("mesh",[]))) and "humans" not in " ".join(meta.get("mesh",[])).lower():
        return None,None,"nonhuman_or_veterinary"
    sid=source_record.get("study_identity",{})
    frozen_companion=(source_record.get("source_family")=="companion_or_secondary"
                      and sid.get("study_identity_cluster_id")
                      and (str(sid.get("study_identity_cluster_id")).startswith("REG:")
                           or sid.get("status") in ("companion_publication","secondary_analysis")))
    if COMP_RE.search(title) or frozen_companion:
        fam="companion_or_secondary"
    elif "practice guideline" in ptypes or "guideline" in ptypes or "consensus statement" in ptypes or "consensus development conference" in ptypes:
        fam="guideline_or_consensus"
    elif "systematic review" in ptypes or "meta-analysis" in ptypes:
        fam="evidence_synthesis"
    elif ("observational study" in ptypes or OBS_RE.search(text)) and not RCT_TITLE_RE.search(title):
        fam="primary_observational"
    elif "randomized controlled trial" in ptypes or "controlled clinical trial" in ptypes or "clinical trial" in ptypes or RCT_TITLE_RE.search(title):
        fam="primary_interventional"
    else:
        return None,None,"unmappable_calibration_family"
    # Domain is calibration-specific and source-grounded. Use title/abstract/MeSH
    # plus the frozen source title as fallback; this prevents parser sparsity from
    # collapsing the whole corpus into "external".
    domain_text=title+" "+abstract+" "+mesh_text+" "+(source_record.get("title") or "")
    dom="nutrition_metabolic_cardiometabolic" if (TITLE_NUTRI_RE.search(domain_text) or MESH_NUTRI_RE.search(domain_text)) else "external_biomedical_or_public_health"
    return fam,dom,None

u=json.loads(UNIVERSE.read_text())
g=json.loads(GOLD100.read_text())

gold_ids={a["candidate_id"] for a in g["assignments"]}
gold_clusters={a.get("study_identity_cluster_id") or a["candidate_id"] for a in g["assignments"]}

pre_candidates=[]
leakage_excluded=[]
for r in u["records"]:
    cid=r["candidate_id"]
    cluster=r.get("study_identity",{}).get("study_identity_cluster_id") or cid
    if cid in gold_ids:
        continue
    if cluster in gold_clusters:
        leakage_excluded.append({"candidate_id":cid,"reason":"shared_StudyIdentityCluster_with_Gold100","cluster":cluster})
        continue
    pre_candidates.append(r)

meta=pubmed_meta([r.get("pmid") for r in pre_candidates if r.get("pmid")])
candidates=[]
semantic_excluded=[]
semantic_reclassified=[]
for r in pre_candidates:
    m=meta.get(r.get("pmid"),{})
    fam,dom,reason=semantic_classification(m,r)
    if reason:
        semantic_excluded.append({"candidate_id":r["candidate_id"],"pmid":r.get("pmid"),"reason":reason,"title":m.get("title") or r.get("title")})
        continue
    rr=json.loads(json.dumps(r))
    old_fam,old_dom=rr.get("source_family"),rr.get("domain")
    rr["calibration_source_family"]=fam
    rr["calibration_domain"]=dom
    tags=json.loads(json.dumps(rr.get("challenge_tags",{})))
    cluster=rr.get("study_identity",{}).get("study_identity_cluster_id")
    identity_status=rr.get("study_identity",{}).get("status")
    if fam=="companion_or_secondary" and cluster and (str(cluster).startswith("REG:") or identity_status in ("companion_publication","secondary_analysis")):
        tags["StudyIdentity_dependency"]=True
    rr["calibration_challenge_tags"]=tags
    if old_fam!=fam or old_dom!=dom:
        semantic_reclassified.append({"candidate_id":rr["candidate_id"],"pmid":rr.get("pmid"),"old_family":old_fam,"new_family":fam,"old_domain":old_dom,"new_domain":dom})
    candidates.append(rr)

profile={"count":len(candidates),"family":{},"domain":{},"tags":{},"family_domain":{}}
for r in candidates:
    fam=r.get("calibration_source_family"); dom=r.get("calibration_domain")
    profile["family"][fam]=profile["family"].get(fam,0)+1
    profile["domain"][dom]=profile["domain"].get(dom,0)+1
    key=f"{fam}|{dom}"
    profile["family_domain"][key]=profile["family_domain"].get(key,0)+1
    for k,v in r.get("calibration_challenge_tags",{}).items():
        if v: profile["tags"][k]=profile["tags"].get(k,0)+1
print("SEMANTIC_POOL_PROFILE="+json.dumps(profile,sort_keys=True),flush=True)

rounds=["A","B"]
family_quota={
    "primary_interventional":4,
    "primary_observational":2,
    "evidence_synthesis":2,
    "guideline_or_consensus":2,
    "companion_or_secondary":2
}
domain_quota={
    "nutrition_metabolic_cardiometabolic":9,
    "external_biomedical_or_public_health":3
}
challenge_min={
    "numeric_complexity":8,
    "causal_language_risk":2,
    "StudyIdentity_dependency":2,
    "correction_retraction_living_version":2,
    "conflict":2,
    "recommendation_exception":2,
    "temporal_cutoff_sensitive":2
}

model=cp_model.CpModel()
x={}
for rd in rounds:
    for r in candidates:
        x[(rd,r["candidate_id"])]=model.NewBoolVar(f"x__{rd}__{r['candidate_id']}")

# 12 per round.
for rd in rounds:
    model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates)==12)

# Candidate can appear in at most one calibration round.
for r in candidates:
    model.Add(sum(x[(rd,r["candidate_id"])] for rd in rounds)<=1)

# Exact family and domain quotas per round.
for rd in rounds:
    for fam,n in family_quota.items():
        model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates if r.get("calibration_source_family")==fam)==n)
    for dom,n in domain_quota.items():
        model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates if r.get("calibration_domain")==dom)==n)

# Each round includes exactly one naturally incomplete-source case.
for rd in rounds:
    model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates if r.get("calibration_challenge_tags",{}).get("incomplete_source_text"))==1)

# All non-incomplete calibration sources must have frozen full text.
for rd in rounds:
    for r in candidates:
        if not r.get("calibration_challenge_tags",{}).get("incomplete_source_text") and r.get("source_text",{}).get("status")!="official_full_text_frozen":
            model.Add(x[(rd,r["candidate_id"])]==0)

# Challenge coverage per round.
for rd in rounds:
    for tag,n in challenge_min.items():
        model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates if r.get("calibration_challenge_tags",{}).get(tag))>=n)

# No duplicate StudyIdentityCluster across the full 24.
clusters={}
for r in candidates:
    cluster=r.get("study_identity",{}).get("study_identity_cluster_id") or r["candidate_id"]
    clusters.setdefault(cluster,[]).append(r)
for cluster,rs in clusters.items():
    if len(rs)>1:
        model.Add(sum(x[(rd,r["candidate_id"])] for rd in rounds for r in rs)<=1)

# Deterministic seeded ordering; first feasible solution is the selection.
ranked=[]
for rd in rounds:
    for r in candidates:
        cid=r["candidate_id"]
        rank=int.from_bytes(hashlib.sha256(f"{SELECTION_KEY}|{rd}|{cid}".encode()).digest()[:8],"big")
        ranked.append((rank,rd,cid,x[(rd,cid)]))
ranked.sort(key=lambda z:(z[0],z[1],z[2]))
model.AddDecisionStrategy([z[3] for z in ranked],cp_model.CHOOSE_FIRST,cp_model.SELECT_MAX_VALUE)

solver=cp_model.CpSolver()
solver.parameters.num_search_workers=1
solver.parameters.search_branching=cp_model.FIXED_SEARCH
solver.parameters.stop_after_first_solution=True
solver.parameters.max_time_in_seconds=120
status=solver.Solve(model)
if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
    raise SystemExit(f"CALIBRATION_SELECTION_INFEASIBLE:{solver.StatusName(status)}")

by_id={r["candidate_id"]:r for r in candidates}
selected=[]
for rd in rounds:
    rows=[]
    for r in candidates:
        if solver.Value(x[(rd,r["candidate_id"])]):
            rows.append(r)
    rows.sort(key=lambda r:int.from_bytes(hashlib.sha256(f"{SELECTION_KEY}|{rd}|{r['candidate_id']}".encode()).digest()[:8],"big"))
    for i,r in enumerate(rows,1):
        selected.append({
            "calibration_slot_id":f"CAL-{rd}-{i:02d}",
            "round":rd,
            "mode":"guided_training" if rd=="A" else "blinded_reliability_validation",
            "candidate_id":r["candidate_id"],
            "pmid":r.get("pmid"),"pmcid":r.get("pmcid"),"doi":r.get("doi"),
            "title":r.get("title"),"source_family":r.get("calibration_source_family"),"domain":r.get("calibration_domain"),
            "study_identity_cluster_id":r.get("study_identity",{}).get("study_identity_cluster_id"),
            "source_text_status":r.get("source_text",{}).get("status"),
            "worker_visible_text_sha256":r.get("source_text",{}).get("worker_visible_text_sha256"),
            "challenge_tags":r.get("calibration_challenge_tags",{})
        })

selected_ids=[x["candidate_id"] for x in selected]
selected_clusters=[x["study_identity_cluster_id"] or x["candidate_id"] for x in selected]

def round_count(rd,fn):
    return sum(1 for x in selected if x["round"]==rd and fn(x))

audit={"stage":STAGE,"status":"PASS_CALIBRATION24_SOURCE_SET_FROZEN",
       "selection_key":SELECTION_KEY,
       "input":{"sampling_universe_count":len(u["records"]),"gold100_count":len(gold_ids),
                "leakage_safe_pre_semantic_count":len(pre_candidates),"semantic_eligible_candidate_count":len(candidates),"same_study_leakage_excluded_count":len(leakage_excluded),"semantic_excluded_count":len(semantic_excluded),"semantic_reclassified_count":len(semantic_reclassified)},
       "solver":{"engine":"OR-Tools CP-SAT","version":"9.14.6206","num_search_workers":1,
                 "search_branching":"FIXED_SEARCH","stop_after_first_solution":True,"status":solver.StatusName(status)},
       "rounds":{},"checks":{}}
for rd in rounds:
    audit["rounds"][rd]={
      "count":round_count(rd,lambda x:True),
      "family":{f:round_count(rd,lambda x,f=f:x["source_family"]==f) for f in family_quota},
      "domain":{d:round_count(rd,lambda x,d=d:x["domain"]==d) for d in domain_quota},
      "challenge":{t:round_count(rd,lambda x,t=t:x["challenge_tags"].get(t)) for t in list(challenge_min)+["incomplete_source_text"]},
      "full_text_frozen":round_count(rd,lambda x:x["source_text_status"]=="official_full_text_frozen"),
      "incomplete_source":round_count(rd,lambda x:x["challenge_tags"].get("incomplete_source_text"))
    }

audit["checks"]={
  "selected_24":len(selected)==24,
  "unique_candidates":len(selected_ids)==len(set(selected_ids)),
  "unique_study_identity_clusters":len(selected_clusters)==len(set(selected_clusters)),
  "no_Gold100_source_overlap":not any(x in gold_ids for x in selected_ids),
  "no_Gold100_StudyIdentity_overlap":not any((x["study_identity_cluster_id"] or x["candidate_id"]) in gold_clusters for x in selected),
  "round_A_count_12":audit["rounds"]["A"]["count"]==12,
  "round_B_count_12":audit["rounds"]["B"]["count"]==12,
  "round_family_quotas":all(audit["rounds"][rd]["family"]==family_quota for rd in rounds),
  "round_domain_quotas":all(audit["rounds"][rd]["domain"]==domain_quota for rd in rounds),
  "one_incomplete_per_round":all(audit["rounds"][rd]["incomplete_source"]==1 for rd in rounds),
  "challenge_minima":all(audit["rounds"][rd]["challenge"][t]>=n for rd in rounds for t,n in challenge_min.items()),
  "non_incomplete_have_full_text":all(x["source_text_status"]=="official_full_text_frozen" or x["challenge_tags"].get("incomplete_source_text") for x in selected)
}
if not all(audit["checks"].values()):
    raise SystemExit("CALIBRATION_POST_SELECTION_AUDIT_FAILED:"+json.dumps(audit["checks"],sort_keys=True))

source_set={
  "corpus":"Paper_C_Calibration24",
  "version":"v1.0",
  "stage":STAGE,
  "status":"FROZEN_NON_GOLD100_CALIBRATION_SOURCE_SET",
  "gold100_source_set_sha256":SOURCE_SET_SHA,
  "selection_key":SELECTION_KEY,
  "design":{
    "round_A":{"n":12,"mode":"guided_training_after_independent_first_pass"},
    "round_B":{"n":12,"mode":"blinded_reliability_gate"},
    "family_quota_per_round":family_quota,
    "domain_quota_per_round":domain_quota,
    "challenge_minima_per_round":challenge_min,
    "incomplete_source_per_round":1,
    "gold100_SourceArtifact_overlap":0,
    "gold100_StudyIdentityCluster_overlap":0,
    "semantic_gate":"PubMed publication-type + title/abstract/MeSH calibration-specific gate; protocols/nonhuman-unmappable sources excluded"
  },
  "assignments":selected
}
source_set_sha=csha(source_set)
source_set["calibration24_source_set_sha256"]=source_set_sha
audit["semantic_gate"]={"excluded":semantic_excluded,"reclassified":semantic_reclassified}
audit["calibration24_source_set_sha256"]=source_set_sha

(OUT/"Calibration24_Source_Set_FROZEN_v1.0.json").write_text(json.dumps(source_set,indent=2,ensure_ascii=False)+"\n")
(OUT/"Calibration24_Source_Set_SHA256_v1.0.txt").write_text(source_set_sha+"\n")
(OUT/"Calibration24_Selection_Audit_v1.0.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n")
(OUT/"Calibration12A_Training_Manifest_v1.0.json").write_text(json.dumps({"round":"A","mode":"guided_training_after_independent_first_pass","records":[x for x in selected if x["round"]=="A"]},indent=2,ensure_ascii=False)+"\n")
(OUT/"Calibration12B_Reliability_Manifest_v1.0.json").write_text(json.dumps({"round":"B","mode":"blinded_reliability_gate","records":[x for x in selected if x["round"]=="B"]},indent=2,ensure_ascii=False)+"\n")
print(json.dumps(audit,indent=2))

# P0.3 revision: independent PubMed semantic gate for calibration-only family/domain validation

# semantic refinement: calibration domain classification uses title + MeSH primary-topic signal, not free abstract mentions

# semantic refinement: title-only companion signal; report-level observational priority; conservative nutrition-domain mapping

# calibration semantic tag derivation: resolved semantic companion/secondary implies StudyIdentity_dependency

# implementation repair: PubMed metadata fallback + frozen StudyIdentity-supported companion classification
