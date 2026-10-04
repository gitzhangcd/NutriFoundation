#!/usr/bin/env python3
"""P0.3 prespecified reliability scorer.

Input JSON:
{
  "categorical": [{"field": "...", "categories": ["a","b"], "a": "...", "b": "...", "applicable": true}, ...],
  "ordinal": [{"field":"...", "K":5, "a":1, "b":2, "applicable":true}, ...],
  "numeric": [{"field":"...", "a":1.2, "b":1.2, "measure":"RR", "unit":null, "tolerance":0.0, "applicable":true}, ...],
  "spans": [{"object_id":"...", "a_tokens":[1,2], "b_tokens":[1,2,3], "applicable":true}, ...],
  "integrity": {"all_schema_valid":true, "all_locked":true, "cross_visibility_events":0,
                "unauthorized_gold100_accesses":0, "blocking_workbench_defects":0,
                "blocking_protocol_ambiguities":0}
}
"""
import argparse, json, hashlib
from collections import defaultdict

TH={"categorical_ac1":0.80,"ordinal_weighted":0.80,"numeric":0.95,"span_f1":0.85}

def gwet_ac1(rows):
    by=defaultdict(list)
    for r in rows:
        if r.get("applicable",True):
            by[r["field"]].append(r)
    field_results=[]
    for field,rs in sorted(by.items()):
        cats=rs[0].get("categories") or sorted(set([x["a"] for x in rs]+[x["b"] for x in rs]))
        q=len(cats)
        n=len(rs)
        if n==0 or q<2: continue
        pa=sum(1 for x in rs if x["a"]==x["b"])/n
        pk=[]
        for k in cats:
            nk=sum(1 for x in rs if x["a"]==k)+sum(1 for x in rs if x["b"]==k)
            pk.append(nk/(2*n))
        pe=sum(p*(1-p) for p in pk)/(q-1)
        ac1=(pa-pe)/(1-pe) if abs(1-pe)>1e-15 else 1.0
        field_results.append({"field":field,"n":n,"Pa":pa,"Pe":pe,"AC1":ac1})
    if not field_results: return None,field_results
    total=sum(x["n"] for x in field_results)
    return sum(x["AC1"]*x["n"] for x in field_results)/total,field_results

def ordinal(rows):
    vals=[]
    for r in rows:
        if not r.get("applicable",True): continue
        K=int(r["K"])
        if K<2: continue
        vals.append(1-abs(float(r["a"])-float(r["b"]))/(K-1))
    return (sum(vals)/len(vals) if vals else None),len(vals)

def numeric(rows):
    vals=[]
    for r in rows:
        if not r.get("applicable",True): continue
        tol=float(r.get("tolerance",0.0))
        same_measure=r.get("measure_a",r.get("measure"))==r.get("measure_b",r.get("measure"))
        same_unit=r.get("unit_a",r.get("unit"))==r.get("unit_b",r.get("unit"))
        agree=same_measure and same_unit and abs(float(r["a"])-float(r["b"]))<=tol
        vals.append(agree)
    return (sum(vals)/len(vals) if vals else None),len(vals)

def spans(rows):
    vals=[]
    for r in rows:
        if not r.get("applicable",True): continue
        A=set(r.get("a_tokens",[])); B=set(r.get("b_tokens",[]))
        if not A and not B: continue
        if not A or not B:
            vals.append(0.0); continue
        inter=len(A&B)
        p=inter/len(A); rec=inter/len(B)
        vals.append(2*p*rec/(p+rec) if p+rec else 0.0)
    return (sum(vals)/len(vals) if vals else None),len(vals)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    data=json.load(open(args.input))
    ac1,fields=gwet_ac1(data.get("categorical",[]))
    ow,on=ordinal(data.get("ordinal",[]))
    na,nn=numeric(data.get("numeric",[]))
    sf,sn=spans(data.get("spans",[]))
    integ=data.get("integrity",{})
    integrity_pass=(
        integ.get("all_schema_valid") is True and
        integ.get("all_locked") is True and
        integ.get("cross_visibility_events",1)==0 and
        integ.get("unauthorized_gold100_accesses",1)==0 and
        integ.get("blocking_workbench_defects",1)==0 and
        integ.get("blocking_protocol_ambiguities",1)==0
    )
    metrics={
      "critical_categorical_Gwet_AC1":ac1,
      "ordinal_weighted_agreement":ow,
      "numeric_agreement":na,
      "source_span_token_F1":sf
    }
    denominators={"categorical":sum(x["n"] for x in fields),"ordinal":on,"numeric":nn,"span":sn}
    estimable=all(v is not None for v in metrics.values())
    gates={
      "categorical":ac1 is not None and ac1>=TH["categorical_ac1"],
      "ordinal":ow is not None and ow>=TH["ordinal_weighted"],
      "numeric":na is not None and na>=TH["numeric"],
      "span":sf is not None and sf>=TH["span_f1"],
      "integrity":integrity_pass
    }
    status="PASS_PRE_GOLD100_ANNOTATION_LOCK" if estimable and all(gates.values()) else ("NON_ESTIMABLE_BLOCK" if not estimable else "FAIL_RELIABILITY_GATE")
    out={"stage":"E0.4.3-P0.3","status":status,"metrics":metrics,"denominators":denominators,
         "categorical_field_results":fields,"thresholds":TH,"gates":gates,"integrity":integ,
         "basis":"Calibration12B locked pre-adjudication records"}
    canon=json.dumps(out,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    out["report_sha256"]=hashlib.sha256(canon.encode()).hexdigest()
    with open(args.output,"w") as f: json.dump(out,f,indent=2,ensure_ascii=False)
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=="__main__": main()
