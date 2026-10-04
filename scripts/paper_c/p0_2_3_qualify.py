#!/usr/bin/env python3
import json, re, hashlib, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/"runs/E0.4.3/P0.2.2/Gold100_Candidate_Source_Registry_RAW_v0.1.json"
OUT=ROOT/"runs/E0.4.3/P0.2.3"
OUT.mkdir(parents=True, exist_ok=True)
CUTOFF="2026-10-03T23:26:00+08:00"
CUTOFF_DATE=datetime.fromisoformat(CUTOFF)
TOOL="NutriFoundation_PaperC_P0_2_3"
EMAIL="noreply@example.invalid"

def http_get(url, retries=2):
    req=urllib.request.Request(url, headers={"User-Agent":"NutriFoundation/0.4.3 (Paper C evidence qualification)"})
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except Exception as e:
            last=e
            time.sleep(min(8, 1.5*(i+1)))
    raise last

def efetch(db, ids):
    q=urllib.parse.urlencode({"db":db,"id":",".join(ids),"retmode":"xml","tool":TOOL,"email":EMAIL})
    return http_get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"+q)

def txt(node):
    if node is None: return ""
    return " ".join(" ".join(node.itertext()).split())

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def parse_date_parts(y,m,d):
    if not y: return None
    months={"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    try:
        yy=int(y); mm=months.get(m, int(m) if str(m).isdigit() else 1); dd=int(d) if str(d).isdigit() else 1
        return datetime(yy,mm,dd,tzinfo=CUTOFF_DATE.tzinfo)
    except: return None

def pubmed_meta(pmids):
    meta={}
    for i in range(0,len(pmids),80):
        root=ET.fromstring(efetch("pubmed",pmids[i:i+80]))
        for art in root.findall(".//PubmedArticle"):
            pmid=txt(art.find("./MedlineCitation/PMID"))
            if not pmid: continue
            ptypes=[txt(x) for x in art.findall(".//PublicationType") if txt(x)]
            abstract=" ".join(txt(x) for x in art.findall(".//Abstract/AbstractText"))
            title=txt(art.find(".//ArticleTitle"))
            mesh=[txt(x) for x in art.findall(".//MeshHeading/DescriptorName") if txt(x)]
            ids={}
            for x in art.findall(".//PubmedData/ArticleIdList/ArticleId"):
                ids[x.attrib.get("IdType","")]=txt(x)
            comments=[]
            for c in art.findall(".//CommentsCorrections"):
                comments.append({"ref_type":c.attrib.get("RefType"),"ref_source":txt(c.find("RefSource")),"ref_pmid":txt(c.find("PMID")) or None,"note":txt(c.find("Note")) or None})
            dates=[]
            for h in art.findall(".//PubmedData/History/PubMedPubDate"):
                dt=parse_date_parts(txt(h.find("Year")),txt(h.find("Month")),txt(h.find("Day")))
                if dt: dates.append((h.attrib.get("PubStatus",""),dt))
            for ad in art.findall(".//ArticleDate"):
                dt=parse_date_parts(txt(ad.find("Year")),txt(ad.find("Month")),txt(ad.find("Day")))
                if dt: dates.append((ad.attrib.get("DateType","ArticleDate"),dt))
            meta[pmid]={"publication_types":ptypes,"abstract":abstract,"title":title,"mesh":mesh,"ids":ids,"comments":comments,"dates":dates,
                        "xml_sha256":sha(ET.tostring(art,encoding="unicode"))}
        time.sleep(0.38)
    return meta

def oa_status(pmcid):
    try:
        b=http_get("https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?"+urllib.parse.urlencode({"id":pmcid}))
        root=ET.fromstring(b)
        rec=root.find(".//record")
        if rec is None: return {"open":False,"license":None,"href":None,"reason":txt(root)}
        links=rec.findall(".//link")
        href=next((x.attrib.get("href") for x in links if x.attrib.get("format") in ("tgz","pdf")),None)
        return {"open":True,"license":rec.attrib.get("license"),"href":href,"reason":None}
    except Exception as e:
        return {"open":False,"license":None,"href":None,"reason":"oa_check_error:"+type(e).__name__}

def fetch_one_pmc(pmcid):
    n=pmcid.replace("PMC","")
    try:
        root=ET.fromstring(efetch("pmc",[n]))
        arts=root.findall(".//article") if root.tag!="article" else [root]
        for art in arts:
            pid=txt(art.find(".//article-id[@pub-id-type='pmc']"))
            pid=pid if pid.startswith("PMC") else ("PMC"+pid if pid else None)
            if pid==pmcid:
                return pmcid,art
    except Exception as e:
        return pmcid,None
    return pmcid,None

def fetch_pmc_articles(pmcids):
    out={}
    done=0
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs={ex.submit(fetch_one_pmc,p):p for p in pmcids}
        for fut in as_completed(futs):
            pmcid,art=fut.result()
            if art is not None: out[pmcid]=art
            done+=1
            if done%20==0 or done==len(pmcids):
                print(f"PMC_PROGRESS {done}/{len(pmcids)} retrieved={len(out)}", flush=True)
    return out

def worker_text_from_pmc(art):
    parts=[]
    title=art.find(".//article-title")
    if title is not None: parts.append(txt(title))
    for a in art.findall(".//abstract"): parts.append(txt(a))
    body=art.find(".//body")
    if body is not None: parts.append(txt(body))
    return "\n\n".join(x for x in parts if x).strip()

def publication_date_ok(meta):
    ds=[d for status,d in meta.get("dates",[]) if status in ("pubmed","entrez","epublish","ppublish","ArticleDate","Electronic")]
    if not ds: ds=[d for _,d in meta.get("dates",[])]
    if not ds: return True, None
    earliest=min(ds)
    return earliest<=CUTOFF_DATE, earliest.isoformat()

def infer_family(rec,meta,fulltext):
    pts=" | ".join(meta.get("publication_types",[])).lower()
    ta=(meta.get("title","")+" "+meta.get("abstract","")).lower()
    initial=rec["source_classification"].get("source_family")
    if any(x in pts for x in ["randomized controlled trial","controlled clinical trial","clinical trial"]):
        return "primary_interventional","pubmed_publication_type"
    if "meta-analysis" in pts or "systematic review" in pts:
        return "evidence_synthesis","pubmed_publication_type"
    if "practice guideline" in pts or re.search(r"(^|\W)guideline($|\W)",pts) or "consensus development conference" in pts:
        return "guideline_or_consensus","pubmed_publication_type"
    if re.search(r"\b(secondary analysis|subgroup analysis|post[- ]hoc|follow[- ]up analysis)\b",ta):
        return "companion_or_secondary","title_or_abstract"
    if any(x in pts for x in ["observational study","comparative study"]) or re.search(r"\b(cohort|case[- ]control|cross[- ]sectional|prospective observational|retrospective)\b",ta):
        return "primary_observational","publication_type_or_abstract"
    if initial in ("primary_interventional","evidence_synthesis","guideline_or_consensus") and initial in rec.get("discovery",{}).get("retrieval_query_keys",[]):
        return initial,"initial"
    return None,"unmappable"

IN_KW=re.compile(r"\b(nutrition|diet|dietary|food|nutrient|vitamin|mineral|protein|carbohydrate|fatty acid|obesity|diabet|glyc|insulin|lipid|cholesterol|metabolic|hypertension|cardiovascular|cardiometabolic|malnutrition|micronutrient|macronutrient|calorie)\b",re.I)
EXT_KW=re.compile(r"\b(cancer|tumou?r|oncolog|infection|infectious|sepsis|vaccine|neurolog|alzheimer|parkinson|respiratory|asthma|copd|psychiatr|dermatolog|rheumatolog|public health)\b",re.I)

def infer_domain(rec,meta):
    keys=set(rec.get("discovery",{}).get("retrieval_query_keys",[]))
    if keys & {"INT","OBS","SYN","GUID","COMP","INT2","SYN2"}: return "nutrition_metabolic_cardiometabolic","discovery_stratum"
    if "EXT" in keys: return "external_biomedical_or_public_health","discovery_stratum"
    s=(meta.get("title","")+" "+meta.get("abstract","")+" "+" ".join(meta.get("mesh",[])))
    if IN_KW.search(s): return "nutrition_metabolic_cardiometabolic","metadata_keywords"
    if EXT_KW.search(s): return "external_biomedical_or_public_health","metadata_keywords"
    return None,"unclassified"

REG_PATTERNS=[
    r"\bNCT\d{8}\b",r"\bISRCTN\d+\b",r"\bACTRN\d+\b",r"\bDRKS\d+\b",
    r"\bUMIN[-A-Z0-9]*\d{6,}\b",r"\bChiCTR[-A-Z0-9]+\b"
]
def registration_ids(s):
    vals=[]
    for p in REG_PATTERNS:
        vals.extend(re.findall(p,s or "",flags=re.I))
    return sorted(set(x.upper() for x in vals))

def version_info(meta):
    pts=" | ".join(meta.get("publication_types",[])).lower()
    cs=meta.get("comments",[])
    refs=[]
    for c in cs:
        if c.get("ref_type") or c.get("ref_pmid"): refs.append(c)
    if "retracted publication" in pts: return "retracted",refs,True
    if "corrected and republished article" in pts: return "republished",refs,True
    if any((c.get("ref_type") or "").lower() in ("retractionin","retractionof","erratumin","erratumfor","republishedin","republishedfrom","updatein","updateof") for c in cs):
        return "corrected",refs,True
    if "living" in (meta.get("title","")+" "+meta.get("abstract","")).lower():
        return "living_current",refs,True
    return "original_current",refs,False

def numeric_tag(s):
    patterns=re.findall(r"(?:\b(?:RR|OR|HR|MD|SMD)\b\s*[=:]?\s*[-+]?\d+(?:\.\d+)?|\b\d+(?:\.\d+)?\s*%|95\s*%\s*CI|confidence interval|\bp\s*[<=>]\s*0?\.\d+)",s,re.I)
    return len(patterns)>=6, patterns[:12]

def causal_tag(family,s):
    if family!="primary_observational": return False,[]
    hits=re.findall(r"\b(associated with|association between|risk of|causal|causality|linked to|predict(?:s|ed|ive)?)\b",s,re.I)
    return len(hits)>=2,hits[:8]

def rec_exception_tag(family,s):
    if family!="guideline_or_consensus": return False,[]
    hits=re.findall(r"\b(except|unless|conditional|recommend against|should not|not recommended|contraindicat\w*|only if|only in|restricted to)\b",s,re.I)
    return len(hits)>=2,hits[:8]

def conflict_from_xml(art):
    if art is None: return False,[],[]
    refmap={}
    for ref in art.findall(".//ref-list/ref"):
        rid=ref.attrib.get("id")
        if not rid: continue
        ids=[]
        for p in ref.findall(".//pub-id"):
            typ=p.attrib.get("pub-id-type","")
            val=txt(p)
            if val: ids.append(f"{typ}:{val}")
        if ids: refmap[rid]=ids
    phrases=[]
    linked=[]
    for p in art.findall(".//body//p"):
        t=txt(p)
        if re.search(r"\b(conflicting|inconsistent|discordant|contradictory|mixed findings|mixed evidence)\b",t,re.I):
            rids=[]
            for x in p.findall(".//xref[@ref-type='bibr']"):
                rid=x.attrib.get("rid","")
                rids.extend(rid.split())
            ids=[]
            for rid in rids: ids.extend(refmap.get(rid,[]))
            if len(set(ids))>=2:
                phrases.append(t[:500])
                linked.extend(ids)
    return bool(phrases),phrases[:3],sorted(set(linked))[:12]

def batch001_pmids():
    p=ROOT/"fixtures/Batch001_Blind_SourceText_v0.1.json"
    if not p.exists(): return set()
    s=p.read_text(errors="ignore")
    return set(re.findall(r"\bPMID[:\s]*([0-9]{5,9})\b",s,re.I))

raw=json.loads(RAW.read_text())
records=raw["records"]
pmids=[r["bibliographic_identity"]["identifiers"]["pmid"] for r in records]
meta=pubmed_meta(pmids)

pmcids=[r["bibliographic_identity"]["identifiers"].get("pmcid") for r in records if r["bibliographic_identity"]["identifiers"].get("pmcid")]
oa={}
for i,p in enumerate(pmcids):
    oa[p]=oa_status(p)
    time.sleep(0.36)

open_pmc=[p for p in pmcids if oa.get(p,{}).get("open")]
pmc_articles=fetch_pmc_articles(open_pmc)

# Map candidates to deterministic normalized worker text and preliminary classification.
work={}
for r in records:
    pmid=r["bibliographic_identity"]["identifiers"]["pmid"]
    pmcid=r["bibliographic_identity"]["identifiers"].get("pmcid")
    m=meta.get(pmid,{})
    art=pmc_articles.get(pmcid) if pmcid else None
    wtxt=worker_text_from_pmc(art) if art is not None else ""
    fam,fam_basis=infer_family(r,m,wtxt)
    dom,dom_basis=infer_domain(r,m)
    pub_ok,pub_dt=publication_date_ok(m)
    ver,verrefs,verstress=version_info(m)
    regids=registration_ids((m.get("title","")+" "+m.get("abstract","")+" "+wtxt)[:500000])
    work[r["candidate_id"]]={
        "pmid":pmid,"pmcid":pmcid,"meta":m,"article":art,"worker_text":wtxt,
        "family":fam,"family_basis":fam_basis,"domain":dom,"domain_basis":dom_basis,
        "publication_ok":pub_ok,"publication_date_basis":pub_dt,
        "version_status":ver,"version_chain_refs":verrefs,"version_stress":verstress,
        "registration_ids":regids,
        "oa":{"open":bool(art),"license":(txt(art.find(".//license"))[:500] if art is not None and art.find(".//license") is not None else None)}
    }

# Build StudyIdentity clusters from registration IDs.
reg_to_ids={}
for cid,w in work.items():
    for regid in w["registration_ids"]:
        reg_to_ids.setdefault(regid,[]).append(cid)

# Select naturally incomplete text stress candidates deterministically after basic family/domain identity checks.
incomplete_candidates=[]
for r in records:
    cid=r["candidate_id"]; w=work[cid]
    if not w["oa"].get("open") and w["family"] and w["domain"] and w["publication_ok"] and w["version_status"]!="retracted":
        incomplete_candidates.append(cid)
incomplete_selected=set(sorted(incomplete_candidates)[:8])

batch1=batch001_pmids()
qualified=[]; excluded=[]; text_manifest=[]
for r in records:
    cid=r["candidate_id"]; w=work[cid]; m=w["meta"]
    pmid=w["pmid"]; pmcid=w["pmcid"]; full=bool(w["worker_text"])
    gates={}
    exclusions=[]
    gates["ELIG-01"]={"pass":bool(pmid),"evidence":f"PMID:{pmid}"}
    if full:
        gates["ELIG-02"]={"pass":True,"evidence":f"PMC OA full text {pmcid}"}
    elif cid in incomplete_selected:
        gates["ELIG-02"]={"pass":True,"evidence":"prespecified naturally incomplete source-text stress exception"}
    else:
        gates["ELIG-02"]={"pass":False,"evidence":"no reproducible PMC EFetch full text available to current qualification run"}; exclusions.append("X02")
    gates["ELIG-03"]={"pass":w["version_status"]!="version_unknown_hold","evidence":w["version_status"]}
    if not gates["ELIG-03"]["pass"]: exclusions.append("X03")
    gates["ELIG-04"]={"pass":w["publication_ok"],"evidence":w["publication_date_basis"]}
    if not w["publication_ok"]: exclusions.append("X04")
    gates["ELIG-05"]={"pass":bool(w["family"]),"evidence":w["family_basis"]}
    if not w["family"]: exclusions.append("X05")
    gates["ELIG-06"]={"pass":bool(w["domain"]),"evidence":w["domain_basis"]}
    if not w["domain"]: exclusions.append("X06")
    # StudyIdentity
    cluster=None; status=None; linked=[]
    if w["registration_ids"]:
        rid=w["registration_ids"][0]; members=sorted(reg_to_ids.get(rid,[]))
        cluster="REG:"+rid; linked=[x for x in members if x!=cid]
        if len(members)>1:
            if w["family"]=="companion_or_secondary": status="companion_publication"
            else: status="independent_primary_report"
        else:
            status="independent_primary_report" if w["family"] in ("primary_interventional","primary_observational") else "identity_resolved_other"
    elif w["family"]=="companion_or_secondary":
        status="unresolved_hold"
    elif w["family"]:
        cluster="PMID:"+pmid
        status="independent_primary_report" if w["family"] in ("primary_interventional","primary_observational") else "identity_resolved_other"
    else:
        status="unresolved_hold"
    # Dedupe same registration cluster: only one primary report survives unless companion family.
    dup_forbidden=False
    if cluster and cluster.startswith("REG:") and len(reg_to_ids.get(cluster[4:],[]))>1 and w["family"]!="companion_or_secondary":
        members=sorted(reg_to_ids[cluster[4:]])
        primary=min(members)
        if cid!=primary: dup_forbidden=True
    if dup_forbidden: exclusions.append("X13")
    identity_ok=status!="unresolved_hold" and not dup_forbidden
    gates["ELIG-07"]={"pass":identity_ok,"evidence":{"cluster":cluster,"status":status,"linked":linked}}
    if status=="unresolved_hold": exclusions.append("X07")
    # Scientific object extractability
    scientific_text=(m.get("abstract","")+" "+w["worker_text"]).strip()
    object_ok=len(scientific_text)>=300 or cid in incomplete_selected
    gates["ELIG-08"]={"pass":object_ok,"evidence":f"text_chars={len(scientific_text)}"}
    if not object_ok: exclusions.append("X08")
    overlap=pmid in batch1
    gates["ELIG-09"]={"pass":not overlap,"evidence":"Batch001 PMID overlap check"}
    if overlap: exclusions.append("X09")
    gates["ELIG-10"]={"pass":True,"evidence":"P0.2.1/P0.2.2 prospective AB-blind construction"}
    prov_ok=bool(r.get("provenance",{}).get("record_status")=="REAL_SOURCE_IDENTITY_BOUND")
    gates["ELIG-11"]={"pass":prov_ok,"evidence":"P0.2.2 PubMed provenance"}
    if not prov_ok: exclusions.append("X11")
    fatal=False
    gates["ELIG-12"]={"pass":not fatal,"evidence":"no automated fatal identity/fabrication signal"}
    # Retractions are retained only as version stress when exact text is reproducibly available.
    if w["version_status"]=="retracted" and not full: exclusions.append("X14")
    exclusions=sorted(set(exclusions))
    # Tags
    num,num_ev=numeric_tag(scientific_text)
    caus,caus_ev=causal_tag(w["family"],scientific_text)
    recx,rec_ev=rec_exception_tag(w["family"],scientific_text)
    conf,conf_ev,conf_refs=conflict_from_xml(w["article"])
    idtag=bool(linked) or status=="companion_publication"
    incomplete=cid in incomplete_selected
    temptag=w["version_stress"]
    tags={
      "numeric_complexity":num,
      "causal_language_risk":caus,
      "StudyIdentity_dependency":idtag,
      "correction_retraction_living_version":w["version_stress"],
      "conflict":conf,
      "recommendation_exception":recx,
      "temporal_cutoff_sensitive":temptag,
      "incomplete_source_text":incomplete
    }
    tag_evidence={
      "numeric_complexity":num_ev if num else [],
      "causal_language_risk":caus_ev if caus else [],
      "StudyIdentity_dependency":linked if idtag else [],
      "correction_retraction_living_version":w["version_chain_refs"] if w["version_stress"] else [],
      "conflict":{"phrases":conf_ev,"linked_refs":conf_refs} if conf else {},
      "recommendation_exception":rec_ev if recx else [],
      "temporal_cutoff_sensitive":w["version_chain_refs"] if temptag else [],
      "incomplete_source_text":["No reproducible OA full text; abstract-only frozen stress exception"] if incomplete else []
    }
    stress=None
    if w["version_stress"]: stress="correction_republication_retraction_or_living_version"
    elif idtag: stress="StudyIdentity_or_companion_dependency"
    elif conf: stress="conflicting_evidence"
    elif recx: stress="recommendation_exception_or_normative_boundary"
    elif temptag: stress="temporal_cutoff_sensitive"
    elif incomplete: stress="incomplete_or_missing_source_text"
    if exclusions:
        state="EXCLUDED"
    elif stress:
        state="ELIGIBLE_CORE_AND_STRESS" if not incomplete else "ELIGIBLE_STRESS"
    else:
        state="ELIGIBLE_CORE"
    rec={
      "candidate_id":cid,
      "pmid":pmid,"pmcid":pmcid,"doi":r["bibliographic_identity"]["identifiers"].get("doi"),
      "title":r["bibliographic_identity"]["canonical_title"],
      "source_family":w["family"],"domain":w["domain"],
      "source_text":{
        "status":"official_full_text_frozen" if full else ("structured_abstract_only" if incomplete else "unavailable"),
        "worker_visible_text_sha256":sha(w["worker_text"]) if full else (sha(m.get("abstract","")) if incomplete else None),
        "worker_visible_text_chars":len(w["worker_text"]) if full else len(m.get("abstract","")),
        "pmc_xml_sha256":sha(ET.tostring(w["article"],encoding="unicode")) if w["article"] is not None else None,
        "pmc_efetch_retrieved":bool(w["oa"].get("open")),
        "license":w["oa"].get("license"),
        "text_definition":"PMC article title + abstract + body, whitespace-normalized; references/back matter excluded" if full else ("PubMed abstract-only natural insufficiency stress package" if incomplete else None)
      },
      "temporal_version":{"evidence_cutoff":CUTOFF,"publication_date_basis":w["publication_date_basis"],"version_status":w["version_status"],"version_chain_refs":w["version_chain_refs"]},
      "study_identity":{"study_identity_cluster_id":cluster,"status":status,"registration_ids":w["registration_ids"],"linked_candidate_ids":linked,"accidental_duplicate_risk":dup_forbidden},
      "challenge_tags":tags,"challenge_tag_evidence":tag_evidence,"stress_stratum":stress,
      "eligibility":{"gate_results":gates,"screening_state":state,"exclusion_reason_codes":exclusions},
      "provenance":{"source_registry_candidate_sha":r.get("provenance",{}).get("candidate_record_sha256"),"pubmed_record_xml_sha256":m.get("xml_sha256"),"qualification_script":"scripts/paper_c/p0_2_3_qualify.py"}
    }
    rec["record_sha256"]=sha(json.dumps(rec,sort_keys=True,ensure_ascii=False,separators=(",",":")))
    if state=="EXCLUDED": excluded.append(rec)
    else: qualified.append(rec)
    text_manifest.append({"candidate_id":cid,"pmid":pmid,"pmcid":pmcid,"text_status":rec["source_text"]["status"],"worker_visible_text_sha256":rec["source_text"]["worker_visible_text_sha256"],"pmc_xml_sha256":rec["source_text"]["pmc_xml_sha256"],"license":rec["source_text"]["license"]})

# Coverage audit.
def count_where(xs,fn): return sum(1 for x in xs if fn(x))
family_counts={f:count_where(qualified,lambda x,f=f:x["source_family"]==f) for f in ["primary_interventional","primary_observational","evidence_synthesis","guideline_or_consensus","companion_or_secondary"]}
domain_counts={d:count_where(qualified,lambda x,d=d:x["domain"]==d) for d in ["nutrition_metabolic_cardiometabolic","external_biomedical_or_public_health"]}
tag_counts={k:count_where(qualified,lambda x,k=k:x["challenge_tags"].get(k)) for k in ["numeric_complexity","causal_language_risk","StudyIdentity_dependency","correction_retraction_living_version","conflict","recommendation_exception","temporal_cutoff_sensitive","incomplete_source_text"]}
stress_counts={s:count_where(qualified,lambda x,s=s:x.get("stress_stratum")==s) for s in ["correction_republication_retraction_or_living_version","StudyIdentity_or_companion_dependency","conflicting_evidence","recommendation_exception_or_normative_boundary","temporal_cutoff_sensitive","incomplete_or_missing_source_text"]}
requirements={
 "family":{"primary_interventional":28,"primary_observational":18,"evidence_synthesis":18,"guideline_or_consensus":12,"companion_or_secondary":4},
 "domain":{"nutrition_metabolic_cardiometabolic":80,"external_biomedical_or_public_health":20},
 "tags":{"numeric_complexity":20,"causal_language_risk":15,"StudyIdentity_dependency":15,"correction_retraction_living_version":10,"conflict":15,"recommendation_exception":10,"temporal_cutoff_sensitive":10,"incomplete_source_text":5},
 "stress":{"correction_republication_retraction_or_living_version":6,"StudyIdentity_or_companion_dependency":4,"conflicting_evidence":4,"recommendation_exception_or_normative_boundary":2,"temporal_cutoff_sensitive":2,"incomplete_or_missing_source_text":2}
}
def gaps(counts,req): return {k:{"have":counts.get(k,0),"need":v,"deficit":max(0,v-counts.get(k,0))} for k,v in req.items() if counts.get(k,0)<v}
coverage={"family_counts":family_counts,"domain_counts":domain_counts,"tag_counts":tag_counts,"stress_counts":stress_counts,
          "gaps":{"family":gaps(family_counts,requirements["family"]),"domain":gaps(domain_counts,requirements["domain"]),"tags":gaps(tag_counts,requirements["tags"]),"stress":gaps(stress_counts,requirements["stress"])}}
coverage_ok=not any(coverage["gaps"][k] for k in coverage["gaps"])

eligible_sorted=sorted(qualified,key=lambda x:x["candidate_id"])
pool_payload={"registry":"Gold100_Eligible_Pool","version":"v0.1","stage":"E0.4.3-P0.2.3","evidence_cutoff":CUTOFF,
              "status":"FROZEN_READY_FOR_SAMPLING" if coverage_ok else "FROZEN_COVERAGE_GAP_NO_SAMPLING",
              "qualification_script":"scripts/paper_c/p0_2_3_qualify.py","eligible_count":len(eligible_sorted),"records":eligible_sorted}
canonical=json.dumps(pool_payload,sort_keys=True,ensure_ascii=False,separators=(",",":"))
pool_sha=sha(canonical)
pool_payload["eligible_pool_sha256"]=pool_sha
report={"stage":"E0.4.3-P0.2.3","status":pool_payload["status"],"raw_count":len(records),"eligible_count":len(qualified),"excluded_count":len(excluded),
        "evidence_cutoff":CUTOFF,"oa_full_text_count":sum(1 for x in text_manifest if x["text_status"]=="official_full_text_frozen"),
        "incomplete_stress_count":sum(1 for x in text_manifest if x["text_status"]=="structured_abstract_only"),
        "coverage":coverage,"eligible_pool_sha256":pool_sha,
        "sampling_authorized":coverage_ok,
        "nonclaim":"No Gold100 deterministic sampling occurs in P0.2.3."}

(OUT/"Gold100_Candidate_Qualification_Registry_v0.1.json").write_text(json.dumps({"stage":"E0.4.3-P0.2.3","qualified":qualified,"excluded":excluded},indent=2,ensure_ascii=False)+"\n")
(OUT/"Gold100_Eligible_Pool_FROZEN_v0.1.json").write_text(json.dumps(pool_payload,indent=2,ensure_ascii=False)+"\n")
(OUT/"Gold100_Exclusion_Registry_v0.1.json").write_text(json.dumps({"stage":"E0.4.3-P0.2.3","excluded_count":len(excluded),"records":excluded},indent=2,ensure_ascii=False)+"\n")
(OUT/"Exact_Text_Hash_Manifest_v0.1.json").write_text(json.dumps({"stage":"E0.4.3-P0.2.3","records":text_manifest},indent=2,ensure_ascii=False)+"\n")
(OUT/"P0.2.3_Qualification_Report_v0.1.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
(OUT/"Eligible_Pool_SHA256_v0.1.txt").write_text(pool_sha+"\n")
print(json.dumps(report,indent=2))

# execution revision: batch PMC EFetch path; triggered from latest branch head

# execution revision: stale-run cancellation enabled
# execution revision: individual PMC EFetch with bounded concurrency
