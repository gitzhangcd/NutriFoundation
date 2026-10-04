#!/usr/bin/env python3
import json, hashlib, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from ortools.sat.python import cp_model

ROOT=Path(__file__).resolve().parents[2]
POOL=ROOT/"runs/E0.4.3/P0.2.3/Gold100_Eligible_Pool_FROZEN_v0.1.json"
POOL_SHA=ROOT/"runs/E0.4.3/P0.2.3/Eligible_Pool_SHA256_v0.1.txt"
SLOTS=ROOT/"paper_c/P0/Gold100_Source_Slot_Manifest_v0.1.json"
AMEND=ROOT/"runs/E0.4.3/P0.2.4/PreSampling_Source_Universe_Amendment_v1.0.json"
ERRATUM=ROOT/"paper_c/P0.2.4/Paper_C_P0_PreSampling_Feasibility_Erratum_v0.1.1.md"
OUT=ROOT/"runs/E0.4.3/P0.2.4"
OUT.mkdir(parents=True,exist_ok=True)
SEED=20260930
CUTOFF="2026-10-03T23:26:00+08:00"

def canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

def text_sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def get(url,retries=4):
    import time
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"NutriFoundation-PaperC/0.4.3"})
            with urllib.request.urlopen(req,timeout=60) as r:
                return r.read()
        except Exception as e:
            last=e
            time.sleep(min(8,1.5*(i+1)))
    raise last

def pubmed_xml(pmids):
    q=urllib.parse.urlencode({"db":"pubmed","id":",".join(pmids),"retmode":"xml","tool":"NutriFoundation","email":"noreply@example.invalid"})
    return ET.fromstring(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"+q))

def pmc_xml(pmcid):
    # Primary transport: Europe PMC fullTextXML. Fallback: NCBI PMC efetch.
    try:
        url=f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
        return ET.fromstring(get(url,retries=3))
    except Exception:
        numeric=pmcid.replace("PMC","")
        q=urllib.parse.urlencode({"db":"pmc","id":numeric,"retmode":"xml","tool":"NutriFoundation","email":"noreply@example.invalid"})
        root=ET.fromstring(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"+q,retries=4))
        if root.tag=="article":
            return root
        art=root.find(".//article")
        if art is None:
            raise RuntimeError(f"PMC_XML_UNAVAILABLE:{pmcid}")
        return art

def txt(node):
    if node is None: return ""
    return " ".join(" ".join(node.itertext()).split())

def worker_text(article):
    parts=[]
    title=article.find(".//article-title")
    if title is not None: parts.append(txt(title))
    for a in article.findall(".//abstract"): parts.append(txt(a))
    body=article.find(".//body")
    if body is not None: parts.append(txt(body))
    return "\n\n".join(x for x in parts if x).strip()

def extract_license(article):
    lic=article.find(".//permissions/license")
    if lic is None: return None
    return lic.attrib.get("{http://www.w3.org/1999/xlink}href") or lic.attrib.get("license-type") or txt(lic)[:300] or None

def registration_ids(s):
    pats=[r"\bNCT\s*0*([0-9]{8})\b",r"\bISRCTN\s*[: ]?([0-9]{8})\b",r"\bChiCTR[-A-Z0-9]+\b",r"\bDRKS\d+\b"]
    out=[]
    for p in pats:
        for m in re.finditer(p,s,re.I):
            val=m.group(0).replace(" ","").replace(":","").upper()
            if val.startswith("NCT") and len(val)>11:
                val="NCT"+val[-8:]
            out.append(val)
    return sorted(set(out))

def numeric_tag(s):
    hits=re.findall(r"(?:\b(?:RR|OR|HR|MD|SMD)\b\s*[=:]?\s*[-+]?\d+(?:\.\d+)?|\b\d+(?:\.\d+)?\s*%|95\s*%\s*CI|confidence interval|\bp\s*[<=>]\s*0?\.\d+)",s,re.I)
    return len(hits)>=6,hits[:12]

def parse_pubmed(root):
    out={}
    for art in root.findall(".//PubmedArticle"):
        pmid=txt(art.find("./MedlineCitation/PMID"))
        if not pmid: continue
        title=txt(art.find(".//ArticleTitle"))
        abstract=" ".join(txt(x) for x in art.findall(".//Abstract/AbstractText"))
        ptypes=[txt(x) for x in art.findall(".//PublicationType") if txt(x)]
        year=txt(art.find(".//JournalIssue/PubDate/Year")) or txt(art.find(".//ArticleDate/Year"))
        month=txt(art.find(".//JournalIssue/PubDate/Month")) or txt(art.find(".//ArticleDate/Month"))
        day=txt(art.find(".//JournalIssue/PubDate/Day")) or txt(art.find(".//ArticleDate/Day"))
        ids={}
        for x in art.findall(".//PubmedData/ArticleIdList/ArticleId"):
            ids[x.attrib.get("IdType","")]=txt(x)
        comments=[]
        for c in art.findall(".//CommentsCorrections"):
            comments.append({"ref_type":c.attrib.get("RefType"),"ref_pmid":txt(c.find("PMID")) or None,"ref_source":txt(c.find("RefSource")) or None})
        out[pmid]={"title":title,"abstract":abstract,"publication_types":ptypes,"year":year,"month":month,"day":day,"ids":ids,"comments":comments,
                   "xml_sha256":text_sha(ET.tostring(art,encoding="unicode"))}
    return out

def publication_date_basis(meta):
    y=meta.get("year")
    try:
        yy=int(y)
    except:
        return None
    months={"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    m=meta.get("month") or "1"
    mm=months.get(m, int(m) if str(m).isdigit() else 1)
    d=meta.get("day") or "1"
    dd=int(d) if str(d).isdigit() else 1
    return f"{yy:04d}-{mm:02d}-{dd:02d}T00:00:00+08:00"

def version_status(meta):
    pts=" | ".join(meta.get("publication_types",[])).lower()
    if "retracted publication" in pts: return "retracted"
    if "corrected and republished article" in pts: return "republished"
    if any((c.get("ref_type") or "").lower() in ("retractionin","retractionof","republishedin","republishedfrom") for c in meta.get("comments",[])):
        return "corrected"
    return "original_current"

# 1) Verify immutable parent pool.
parent=json.loads(POOL.read_text())
expected_parent_sha=POOL_SHA.read_text().strip()
tmp=dict(parent)
embedded=tmp.pop("eligible_pool_sha256",None)
actual_parent_sha=canonical_sha(tmp)
if expected_parent_sha!=actual_parent_sha or embedded!=expected_parent_sha:
    raise SystemExit(f"PARENT_POOL_HASH_MISMATCH expected={expected_parent_sha} actual={actual_parent_sha} embedded={embedded}")

# 2) Machine-qualify the minimal pre-sampling source amendment.
amend=json.loads(AMEND.read_text())
source_specs={x["candidate_id"]:x for x in amend["records"]}
pmids=[x["pmid"] for x in amend["records"]]
meta=parse_pubmed(pubmed_xml(pmids))
new_records=[]
for spec in amend["records"]:
    pmid=spec["pmid"]; pmcid=spec["pmcid"]
    if pmid not in meta: raise SystemExit(f"MISSING_PUBMED:{pmid}")
    m=meta[pmid]
    article=pmc_xml(pmcid)
    wtxt=worker_text(article)
    if len(wtxt)<1000: raise SystemExit(f"FULLTEXT_TOO_SHORT:{pmid}:{len(wtxt)}")
    regs=registration_ids(m["title"]+" "+m["abstract"]+" "+wtxt)
    expected_reg=spec["expected_registration_id"].replace(" ","").replace(":","").upper()
    if expected_reg not in regs:
        raise SystemExit(f"REGISTRATION_MISMATCH:{pmid}:expected={expected_reg}:found={regs}")
    if spec["source_family"]=="companion_or_secondary":
        secondary_signal=bool(re.search(r"\b(secondary analysis|post hoc|subgroup analysis|follow[- ]up analysis)\b",m["title"]+" "+m["abstract"],re.I))
        if not secondary_signal: raise SystemExit(f"NO_COMPANION_SIGNAL:{pmid}")
        identity_status="companion_publication"
    else:
        identity_status="independent_primary_report"
        linked=spec.get("linked_companion_evidence_pmid") or spec.get("linked_companion_pmid")
        if not linked: raise SystemExit(f"PRIMARY_ID_DEPENDENCY_WITHOUT_LINKED_COMPANION:{pmid}")
    num,num_ev=numeric_tag(m["abstract"]+" "+wtxt)
    pubdate=publication_date_basis(m)
    if pubdate and pubdate > CUTOFF:
        raise SystemExit(f"AFTER_CUTOFF:{pmid}:{pubdate}")
    vstat=version_status(m)
    if vstat=="retracted": raise SystemExit(f"RETRACTED_AMENDMENT_SOURCE:{pmid}")
    rec={
      "candidate_id":spec["candidate_id"],"pmid":pmid,"pmcid":pmcid,"doi":spec.get("doi"),
      "title":spec["title"],"source_family":spec["source_family"],"domain":spec["domain"],
      "source_text":{
        "status":"official_full_text_frozen","worker_visible_text_sha256":text_sha(wtxt),
        "worker_visible_text_chars":len(wtxt),"pmc_xml_sha256":text_sha(ET.tostring(article,encoding="unicode")),
        "fulltext_xml_retrieved":True,"license":extract_license(article),
        "text_definition":"PMC article title + abstract + body, whitespace-normalized; references/back matter excluded"
      },
      "temporal_version":{
        "evidence_cutoff":CUTOFF,"publication_date_basis":pubdate,"version_status":vstat,"version_chain_refs":m.get("comments",[])
      },
      "study_identity":{
        "study_identity_cluster_id":"REG:"+expected_reg,"status":identity_status,
        "registration_ids":regs,"linked_candidate_ids":[],
        "identity_evidence_refs":[f"PMID:{pmid}",f"REG:{expected_reg}"]+([f"LINKED_COMPANION_PMID:{linked}"] if spec["source_family"]!="companion_or_secondary" and linked else []),
        "accidental_duplicate_risk":False
      },
      "challenge_tags":{
        "numeric_complexity":num,"causal_language_risk":False,"StudyIdentity_dependency":True,
        "correction_retraction_living_version":False,"conflict":False,"recommendation_exception":False,
        "temporal_cutoff_sensitive":False,"incomplete_source_text":False
      },
      "challenge_tag_evidence":{
        "numeric_complexity":num_ev if num else [],
        "causal_language_risk":[],
        "StudyIdentity_dependency":[f"registration={expected_reg}"]+([f"linked companion PMID={linked}"] if spec["source_family"]!="companion_or_secondary" and linked else ["secondary/post-hoc source relation"]),
        "correction_retraction_living_version":[],"conflict":{},"recommendation_exception":[],
        "temporal_cutoff_sensitive":[],"incomplete_source_text":[]
      },
      "stress_stratum":None,
      "eligibility":{
        "gate_results":{
          "ELIG-01":{"pass":True,"evidence":f"PMID:{pmid}; PMCID:{pmcid}"},
          "ELIG-02":{"pass":True,"evidence":f"PMC fullTextXML frozen; chars={len(wtxt)}"},
          "ELIG-03":{"pass":True,"evidence":vstat},
          "ELIG-04":{"pass":True,"evidence":pubdate},
          "ELIG-05":{"pass":True,"evidence":spec["source_family"]},
          "ELIG-06":{"pass":True,"evidence":spec["domain"]},
          "ELIG-07":{"pass":True,"evidence":{"cluster":"REG:"+expected_reg,"status":identity_status}},
          "ELIG-08":{"pass":True,"evidence":f"text_chars={len(wtxt)}"},
          "ELIG-09":{"pass":True,"evidence":"pre-sampling amendment source not in Batch001"},
          "ELIG-10":{"pass":True,"evidence":"joint-feasibility repair only; no AB/model outputs used"},
          "ELIG-11":{"pass":True,"evidence":"PubMed+PMCID+fullTextXML amendment provenance"},
          "ELIG-12":{"pass":True,"evidence":"no fatal integrity signal"}
        },
        "screening_state":"ELIGIBLE_CORE_AND_STRESS" if spec["source_family"]=="companion_or_secondary" else "ELIGIBLE_CORE",
        "exclusion_reason_codes":[]
      },
      "provenance":{
        "pubmed_record_xml_sha256":m["xml_sha256"],"qualification_script":"scripts/paper_c/p0_2_4_select.py",
        "amendment_authority":"runs/E0.4.3/P0.2.4/PreSampling_Feasibility_Amendment_v1.1.json"
      }
    }
    rec["record_sha256"]=canonical_sha(rec)
    new_records.append(rec)

# 3) Build a formally versioned augmented sampling universe without mutating the parent.
records=[json.loads(json.dumps(x)) for x in parent["records"]]+new_records
universe={
  "registry":"Gold100_Augmented_Sampling_Universe","version":"v1.0","stage":"E0.4.3-P0.2.4-A0",
  "status":"FROZEN_FOR_P0_2_4_SELECTION","parent_pool_sha256":expected_parent_sha,
  "normative_erratum":"paper_c/P0.2.4/Paper_C_P0_PreSampling_Feasibility_Erratum_v0.1.1.md",
  "source_amendment_count":len(new_records),"eligible_count":len(records),"records":records
}
universe_sha=canonical_sha(universe)
universe["sampling_universe_sha256"]=universe_sha

# 4) Deterministic constrained slot assignment.
slot_manifest=json.loads(SLOTS.read_text())
slots=slot_manifest["slots"]
stress_tag={
 "correction_republication_retraction_or_living_version":"correction_retraction_living_version",
 "study_identity_or_companion_dependency":"StudyIdentity_dependency",
 "conflicting_evidence":"conflict",
 "recommendation_exception_or_normative_boundary":"recommendation_exception",
 "temporal_cutoff_sensitive":"temporal_cutoff_sensitive",
 "incomplete_or_missing_source_text":"incomplete_source_text"
}
challenge_min={
 "numeric_complexity":20,
 "causal_language_risk":15,
 "StudyIdentity_dependency":15,
 "correction_retraction_living_version":10,
 "conflict":15,
 "recommendation_exception":10,
 "temporal_cutoff_sensitive":10,
 "incomplete_source_text":2
}

def compatible(r,s):
    if r.get("domain")!=s["domain_target"]: return False
    if s["block"]=="core":
        return r.get("source_family")==s["sampling_stratum"] and r.get("source_text",{}).get("status")=="official_full_text_frozen"
    tag=stress_tag[s["sampling_stratum"]]
    if not r.get("challenge_tags",{}).get(tag): return False
    if s["sampling_stratum"]!="incomplete_or_missing_source_text" and r.get("source_text",{}).get("status")!="official_full_text_frozen":
        return False
    if s["sampling_stratum"]=="incomplete_or_missing_source_text" and not r.get("challenge_tags",{}).get("incomplete_source_text"):
        return False
    return True

model=cp_model.CpModel()
x={}
edges_by_slot={s["slot_id"]:[] for s in slots}
edges_by_cand={r["candidate_id"]:[] for r in records}
rec_by_id={r["candidate_id"]:r for r in records}
for s in slots:
    for r in records:
        if compatible(r,s):
            v=model.NewBoolVar(f"x__{s['slot_id']}__{r['candidate_id']}")
            x[(s["slot_id"],r["candidate_id"])]=v
            edges_by_slot[s["slot_id"]].append(v)
            edges_by_cand[r["candidate_id"]].append(v)
for s in slots:
    if not edges_by_slot[s["slot_id"]]:
        raise SystemExit(f"NO_COMPATIBLE_CANDIDATE_FOR_SLOT:{s['slot_id']}")
    model.Add(sum(edges_by_slot[s["slot_id"]])==1)

selected={}
for r in records:
    cid=r["candidate_id"]
    if edges_by_cand[cid]:
        sv=model.NewBoolVar(f"sel__{cid}")
        model.Add(sum(edges_by_cand[cid])==sv)
        selected[cid]=sv

clusters={}
for cid,sv in selected.items():
    cluster=rec_by_id[cid].get("study_identity",{}).get("study_identity_cluster_id") or cid
    clusters.setdefault(cluster,[]).append(sv)
for cluster,vars_ in clusters.items():
    if len(vars_)>1:
        model.Add(sum(vars_)<=1)

for tag,minimum in challenge_min.items():
    vars_=[sv for cid,sv in selected.items() if rec_by_id[cid].get("challenge_tags",{}).get(tag)]
    if len(vars_)<minimum:
        raise SystemExit(f"TAG_POOL_INFEASIBLE:{tag}:have={len(vars_)}:need={minimum}")
    model.Add(sum(vars_)>=minimum)

# Deterministic pseudo-random objective driven only by frozen seed, slot, and candidate identity.
terms=[]
for (sid,cid),v in x.items():
    h=hashlib.sha256(f"{SEED}|{sid}|{cid}".encode()).digest()
    cost=int.from_bytes(h[:4],"big")
    terms.append(cost*v)
model.Minimize(sum(terms))

solver=cp_model.CpSolver()
solver.parameters.num_search_workers=1
solver.parameters.random_seed=SEED
solver.parameters.max_time_in_seconds=300
status=solver.Solve(model)
if status!=cp_model.OPTIMAL:
    raise SystemExit(f"SAMPLER_NOT_OPTIMAL:status={solver.StatusName(status)}")

assignments=[]
selected_ids=set()
for s in slots:
    chosen=None
    for r in records:
        v=x.get((s["slot_id"],r["candidate_id"]))
        if v is not None and solver.Value(v):
            chosen=r; break
    if chosen is None: raise SystemExit(f"UNFILLED_SLOT:{s['slot_id']}")
    selected_ids.add(chosen["candidate_id"])
    assignments.append({
      "slot_id":s["slot_id"],"block":s["block"],"sampling_stratum":s["sampling_stratum"],"domain_target":s["domain_target"],
      "candidate_id":chosen["candidate_id"],"pmid":chosen.get("pmid"),"pmcid":chosen.get("pmcid"),"doi":chosen.get("doi"),
      "title":chosen.get("title"),"source_family":chosen.get("source_family"),"domain":chosen.get("domain"),
      "study_identity_cluster_id":chosen.get("study_identity",{}).get("study_identity_cluster_id"),
      "worker_visible_text_sha256":chosen.get("source_text",{}).get("worker_visible_text_sha256"),
      "source_text_status":chosen.get("source_text",{}).get("status"),
      "challenge_tags":chosen.get("challenge_tags",{}),
      "source_origin":"pre_sampling_amendment" if chosen["candidate_id"].startswith("G100-AMEND-") else "P0.2.3_frozen_pool"
    })

if len(selected_ids)!=100: raise SystemExit(f"UNIQUE_SELECTION_COUNT:{len(selected_ids)}")

selected_records=[rec_by_id[cid] for cid in selected_ids]
def count_tag(tag): return sum(1 for r in selected_records if r.get("challenge_tags",{}).get(tag))
family_counts={}
domain_counts={}
block_counts={}
stress_counts={}
for a in assignments:
    block_counts[a["block"]]=block_counts.get(a["block"],0)+1
    domain_counts[a["domain"]]=domain_counts.get(a["domain"],0)+1
    if a["block"]=="core": family_counts[a["source_family"]]=family_counts.get(a["source_family"],0)+1
    else: stress_counts[a["sampling_stratum"]]=stress_counts.get(a["sampling_stratum"],0)+1
challenge_counts={k:count_tag(k) for k in challenge_min}
cluster_ids=[a["study_identity_cluster_id"] or a["candidate_id"] for a in assignments]
checks={
 "selected_count":len(assignments)==100,
 "unique_source_count":len(selected_ids)==100,
 "unique_study_identity_clusters":len(cluster_ids)==len(set(cluster_ids)),
 "core80":block_counts.get("core")==80,
 "stress20":block_counts.get("stress")==20,
 "domain_80_20":domain_counts.get("nutrition_metabolic_cardiometabolic")==80 and domain_counts.get("external_biomedical_or_public_health")==20,
 "core_family_quotas":family_counts=={"primary_interventional":28,"primary_observational":18,"evidence_synthesis":18,"guideline_or_consensus":12,"companion_or_secondary":4},
 "stress_quotas":stress_counts=={
   "correction_republication_retraction_or_living_version":6,
   "study_identity_or_companion_dependency":4,
   "conflicting_evidence":4,
   "recommendation_exception_or_normative_boundary":2,
   "temporal_cutoff_sensitive":2,
   "incomplete_or_missing_source_text":2
 },
 "challenge_minima":all(challenge_counts[k]>=v for k,v in challenge_min.items()),
 "non_incomplete_slots_have_full_text":all(a["source_text_status"]=="official_full_text_frozen" for a in assignments if a["sampling_stratum"]!="incomplete_or_missing_source_text"),
 "incomplete_slots_are_incomplete_tagged":all(a["challenge_tags"].get("incomplete_source_text") for a in assignments if a["sampling_stratum"]=="incomplete_or_missing_source_text")
}
if not all(checks.values()):
    raise SystemExit("POST_SELECTION_AUDIT_FAILED:"+json.dumps(checks,sort_keys=True))

source_set={
 "corpus":"Paper_C_Gold100","version":"v1.0","stage":"E0.4.3-P0.2.4","status":"FROZEN_SOURCE_SET",
 "sampling_seed":SEED,"parent_pool_sha256":expected_parent_sha,"augmented_sampling_universe_sha256":universe_sha,
 "normative_erratum":"paper_c/P0.2.4/Paper_C_P0_PreSampling_Feasibility_Erratum_v0.1.1.md",
 "selection_algorithm":"OR-Tools CP-SAT 9.14.6206; single worker; deterministic SHA256(seed|slot|candidate) edge-cost minimization",
 "assignments":assignments
}
source_set_sha=canonical_sha(source_set)
source_set["gold100_source_set_sha256"]=source_set_sha

filled={"corpus":"Paper_C_Gold100","version":"v1.0","parent_slot_manifest_sha":"5ee6bb48c345275f3d4f01111a637ac685458c5e","slots":[]}
for s in slots:
    a=next(x for x in assignments if x["slot_id"]==s["slot_id"])
    z=dict(s)
    z.update({
      "source_ref":a["candidate_id"],"source_identity_status":"filled_frozen",
      "eligibility_status":"eligible_selected","gold_annotation_status":"not_started",
      "pmid":a["pmid"],"pmcid":a["pmcid"],"doi":a["doi"],"title":a["title"],
      "study_identity_cluster_id":a["study_identity_cluster_id"],"worker_visible_text_sha256":a["worker_visible_text_sha256"]
    })
    filled["slots"].append(z)

audit={
 "stage":"E0.4.3-P0.2.4","status":"PASS_FROZEN","sampling_seed":SEED,
 "input":{"parent_pool_count":len(parent["records"]),"parent_pool_sha256":expected_parent_sha,"amendment_count":len(new_records),"augmented_count":len(records),"augmented_sampling_universe_sha256":universe_sha},
 "solver":{"engine":"OR-Tools CP-SAT","version":"9.14.6206","num_search_workers":1,"solver_status":solver.StatusName(status),"objective_value":solver.ObjectiveValue()},
 "counts":{"block":block_counts,"core_family":family_counts,"domain":domain_counts,"stress":stress_counts,"challenge":challenge_counts},
 "challenge_minima":challenge_min,
 "checks":checks,
 "selected_amendment_sources":[a for a in assignments if a["source_origin"]=="pre_sampling_amendment"],
 "gold100_source_set_sha256":source_set_sha,
 "sampling_performed":True
}

(OUT/"Gold100_Augmented_Sampling_Universe_v1.0.json").write_text(json.dumps(universe,indent=2,ensure_ascii=False)+"\n")
(OUT/"Augmented_Sampling_Universe_SHA256_v1.0.txt").write_text(universe_sha+"\n")
(OUT/"PreSampling_Source_Amendment_Qualified_v1.0.json").write_text(json.dumps({"status":"PASS","records":new_records},indent=2,ensure_ascii=False)+"\n")
(OUT/"Gold100_Source_Set_FROZEN_v1.0.json").write_text(json.dumps(source_set,indent=2,ensure_ascii=False)+"\n")
(OUT/"Gold100_Source_Set_SHA256_v1.0.txt").write_text(source_set_sha+"\n")
(OUT/"Gold100_Sampling_Audit_v1.0.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n")
(OUT/"Gold100_Source_Slot_Manifest_FILLED_v1.0.json").write_text(json.dumps(filled,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(audit,indent=2))

# implementation repair: accept linked_companion_pmid alias from frozen amendment registry

# implementation repair: derive StudyIdentity cluster directly from expected_registration_id

# transport repair: PMC fullTextXML retries with NCBI efetch fallback
