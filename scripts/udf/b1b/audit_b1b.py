#!/usr/bin/env python3
"""Independent internal consistency and source code-domain audit for U2-B.
All record-level flags stay local. Thresholds are exploratory export diagnostics, not
measurement-validity or research eligibility thresholds; no source value is repaired.
"""
import argparse,csv,json,collections as C,pathlib as P,sys,zipfile,re,hashlib
from decimal import Decimal as D
HERE=P.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"b1"),str(HERE)]
from run_b1b import verify_inputs,INPUT,ASA_MEMBER,ASA_MEMBER_SHA,atomic_json,file_sha
from contract import require,ref,resolve,canon
from semantics import numeric
THRESHOLDS=(D("0.000001"),D("0.01"),D("0.1"))
FIELDS=(("energy",1,3,"kcal"),("mass",2,2,"g"),("fat",3,4,"g"),("carb",4,5,"g"),("protein",5,6,"g"))
def rd(p):
    with p.open(encoding="utf-8-sig",newline="") as h:return list(csv.reader(h))
def errors(values):
    return {"comparisons":len(values),"exact":sum(x==0 for x in values),
            "within_exploratory_thresholds":{str(t):sum(x<=t for x in values) for t in THRESHOLDS},
            "max_abs_difference":str(max(values,default=D(0)))}
def gate_flag(delta):
    return "HOLD_SOURCE_TOTAL_CONFLICT" if abs(delta)>D("0.01") else "WITHIN_EXPLORATORY_TOLERANCE_NOT_QUALIFIED"
def total_guard(flag):
    require(flag!="HOLD_SOURCE_TOTAL_CONFLICT","SOURCE_TOTAL_CONFLICT")
    require(flag=="WITHIN_EXPLORATORY_TOLERANCE_NOT_QUALIFIED","SOURCE_TOTAL_FLAG_UNRESOLVED")
    return "ARITHMETIC_DIAGNOSTIC_ONLY"
def fndds_candidate(raw,declared_system):
    require(isinstance(raw,str) and re.fullmatch(r"[0-9]{8}",raw) is not None,"FNDDS_CODE_LEXICAL")
    require(declared_system=="FNDDS_2015_16_DECLARED_BY_ASA24_2020","FNDDS_VERSION_MISMATCH")
    return {"native_code":raw,"candidate_system":declared_system,"external_join":"HOLD_NO_TARGET_RELEASE_AUDITED"}
def main(root,out):
    root=root.resolve();out=out.resolve();require(out.is_dir(),"U2B_RUN_NOT_FOUND")
    objs,idx,resolver=verify_inputs(root)
    paths={k:root/v["path"] for k,v in resolver.items()}
    names={p.name:(r,p) for r,p in paths.items()}
    p=names["ingredients_metadata.csv"][1];ing=rd(p)
    require(ing[0]==["ingr","id","cal/g","fat(g)","carb(g)","protein(g)"],"N5K_ING_HEADER")
    parents={"ingr_"+r[1].zfill(10):[D(v) for v in r[2:]] for r in ing[1:]}
    require(len(parents)==555,"N5K_PARENT_KEY")
    full_line=C.defaultdict(list);all_totals=C.defaultdict(list);site_reports={};flags={};private_flags=[];full_dishes=0;full_lines=0
    for cafe in ("cafe1","cafe2"):
        ar,p=names["dish_metadata_"+cafe+".csv"]
        rows=rd(p);es=C.defaultdict(list);signed=C.defaultdict(C.Counter);patterns=C.Counter();held=0
        for ri,r in enumerate(rows,1):
            require(len(r)>=13 and (len(r)-6)%7==0,"N5K_DISH_LAYOUT")
            lines=[r[j:j+7] for j in range(6,len(r),7)]
            full_dishes+=1;full_lines+=len(lines);bad=[]
            for k,j,col,unit in FIELDS:
                delta=D(r[j])-sum((D(v[col]) for v in lines),D(0));es[k].append(abs(delta));all_totals[k].append(abs(delta))
                q=gate_flag(delta);flags[(ar,ri,k)]=q
                if q=="HOLD_SOURCE_TOTAL_CONFLICT":
                    bad.append(k);signed[k]["total_gt_sum" if delta>0 else "total_lt_sum"]+=1
                    private_flags.append({"source_artifact_ref":ar,"csv_record":ri,"dish_id":r[0],"field":k,"unit":unit,"source_total":r[j],"ingredient_sum":str(D(r[j])-delta),"absolute_difference":str(abs(delta)),"flag":q})
            patterns[",".join(bad) if bad else "ALL_WITHIN_0.01"]+=1;held+=bool(bad)
            for v in lines:
                require(v[0] in parents,"N5K_MISSING_INGREDIENT_PARENT")
                parent=parents[v[0]]
                for j,k in enumerate(("energy","fat","carb","protein")):
                    full_line[k].append(abs(D(v[3+j])-D(v[2])*parent[j]))
        site_reports[cafe]={"dish_rows":len(rows),"any_total_conflict":held,"all_totals_within_0.01":len(rows)-held,
                            "field_comparisons":{k:dict(errors(v),conflict_directions=dict(signed[k])) for k,v in es.items()},"pattern_counts":dict(patterns)}
    require(full_dishes==5006 and full_lines==28455,"N5K_FULL_COUNTS")
    require(all(len(v)==full_lines for v in full_line.values()),"N5K_LINE_COUNT")
    selected=C.Counter();selected_flags=[]
    for o in objs:
        if o["kind"]!="NutrientMeasurementDraft":continue
        p=o["payload"];k=p["component_key"]
        if not k.startswith("fallback:Nutrition5k:dish:") or ":ingredient:" in k:continue
        n=resolve(idx,p["native_ref"],"NativeRecord")["payload"]
        q=flags[(n["artifact_ref"],n["locator"]["csv_record"],k.rsplit(":",1)[-1])]
        selected[q]+=1
        selected_flags.append({"measurement_ref":ref(o),"source_artifact_ref":n["artifact_ref"],"csv_record":n["locator"]["csv_record"],"field":k.rsplit(":",1)[-1],"flag":q})
    require(sum(selected.values())==165,"N5K_SELECTED_TOTAL_COUNT")
    for p in (out/"private/N5kTotalConflictFlags.jsonl",out/"private/N5kSelectedTotalFlags.jsonl"):
        require(not p.exists(),"AUDIT_OUTPUT_EXISTS")
    def write_lines(p,seq):
        with p.open("x",encoding="utf8") as h:
            for v in seq:h.write(canon(v)+"\n")
    write_lines(out/"private/N5kTotalConflictFlags.jsonl",private_flags)
    write_lines(out/"private/N5kSelectedTotalFlags.jsonl",selected_flags)
    n5={"source":"Nutrition5k original fallback; no N5k360 geometry qualification",
        "source_layout":"6 fixed columns + 7 fields per ingredient; source README layout wording differs",
        "exploratory_thresholds":[str(x) for x in THRESHOLDS],
        "threshold_boundary":"0.01 in field-specific source units used to flag conflicts only; not a scientific accuracy threshold",
        "dish_rows":full_dishes,"ingredient_rows":full_lines,"ingredient_reference_count":len(parents),
        "ingredient_arithmetic":{k:errors(v) for k,v in full_line.items()},
        "dish_total_vs_line_sum":{k:errors(v) for k,v in all_totals.items()},"cafe_stratification":site_reports,
        "dish_rows_any_total_conflict":sum(x["any_total_conflict"] for x in site_reports.values()),
        "selected_u2a_total_measurement_flags":dict(selected),"selected_total_measurements":sum(selected.values()),
        "record_level_hold_policy":"flagged totals not accepted as reference or automatically corrected; preserve source totals and ingredient sums separately",
        "scope":"source-internal arithmetic only; no independent chemical truth, mass acquisition validation or scan group validation"}
    # SNAPMe versioned code domain and composite-key audit, no inferred intake totals.
    p=names["master_SNAPME_linkfile.csv"][1]
    with p.open(encoding="utf-8-sig",newline="") as h:rows=list(csv.DictReader(h))
    require(len(rows)==4761,"SNAPME_FULL_COUNT")
    candidates=[("subject_id","snapme_study_day","Occ_No","FoodNum1"),
                ("subject_id","snapme_study_day","Occ_No","FoodNum1","FoodCode"),
                ("subject_id","snapme_study_day","Occ_No","FoodNum1","FoodCode","CodeNum","ModCode")]
    kstats=[]
    for keys in candidates:
        c=C.Counter(tuple(r[k] for k in keys) for r in rows)
        kstats.append({"fields":list(keys),"distinct":len(c),"duplicate_groups":sum(x>1 for x in c.values()),"max_multiplicity":max(c.values()),"blank_key_rows":sum(any(not r[k].strip() for k in keys) for r in rows)})
    # Re-open exact official field dictionary version.
    sys.path.insert(0,str(root/INPUT/"xlrd_vendor"))
    import xlrd
    with zipfile.ZipFile(root/INPUT/"ASA24_2020.zip") as z:b=z.read(ASA_MEMBER)
    require(hashlib.sha256(b).hexdigest()==ASA_MEMBER_SHA,"ASA24_MEMBER_HASH")
    sh=xlrd.open_workbook(file_contents=b).sheet_by_name("DATADICTIONARY")
    expected={"OCC_NO":12,"FOODNUM":18,"FOODTYPE":19,"CODENUM":21,"FOODCODE":22,"MODCODE":23}
    dictionary=[]
    for k,i in expected.items():
        r=sh.row_values(i-1);require(str(r[0]).strip().upper()==k,"ASA24_CODE_FIELD_LOCATOR")
        dictionary.append({"field":k,"worksheet":"DATADICTIONARY","row":i,"description":str(r[1]).strip()})
    domain="FNDDS_2015_16_DECLARED_BY_ASA24_2020"
    good=0;bad=0
    for r in rows:
        try:fndds_candidate(r["FoodCode"],domain);good+=1
        except ValueError:bad+=1
    selected_codes=[];selected_code_hold=0
    for o in objs:
        if o["kind"]!="DietaryObservationDraft":continue
        raw=o["payload"]["bindings"]["FoodCode"]["raw_value"]
        try:code=fndds_candidate(raw,domain)
        except ValueError:
            code={"native_code":raw,"candidate_system":"UNRESOLVED_SOURCE_CODE_DOMAIN","external_join":"HOLD_NON_FNDDS_LEXICAL_FORMAT"};selected_code_hold+=1
        selected_codes.append({"observation_ref":ref(o),**code})
    write_lines(out/"private/SNAPMeFNDDSCodeCandidates.jsonl",selected_codes)
    sn={"rows":len(rows),"exact_full_row_distinct":len({tuple(r.values()) for r in rows}),
        "food_amount_duplicate_columns_equal_rows":sum(r["FoodAmt"]==r["FoodAmt.1"] for r in rows),
        "key_profiles":kstats,"code_lexical_8_digit_rows":good,"code_invalid_lexical_rows":bad,
        "distinct_nonblank_food_codes":len({r["FoodCode"] for r in rows if r["FoodCode"].strip()}),
        "source_code_namespace_candidate":domain,"external_target_join":"HOLD_NO_ACTUAL_FNDDS_2015_16_TARGET_AUDITED",
        "foodnum1_vs_foodnum":"rename/derivation semantics not proven","selected_code_records":len(selected_codes),"selected_code_candidates":len(selected_codes)-selected_code_hold,"selected_code_hold":selected_code_hold,
        "non8_digit_code_length_counts":dict(C.Counter(str(len(r["FoodCode"])) for r in rows if re.fullmatch(r"[0-9]{8}",r["FoodCode"]) is None)),
        "distinct_non8_digit_codes":len({r["FoodCode"] for r in rows if re.fullmatch(r"[0-9]{8}",r["FoodCode"]) is None}),
        "non8_digit_code_policy":"Preserve raw token; no zero padding, no assumed supplement identity, no FNDDS join.",
        "official_field_dictionary_rows_verified":dictionary,
        "interpretation":"full-key unique in current file only, not proved intake-event identity; no aggregation or long-term state inference"}
    report={"run_id":"B1-U2B-SOURCE-CONSISTENCY-001","nutrition5k":n5,"snapme":sn,"source_files_unchanged":all(file_sha(root/v["path"])==v["sha256"] for v in resolver.values()),"research_reference_qualified":False}
    require(report["source_files_unchanged"],"SOURCE_MUTATION")
    atomic_json(out/"SourceConsistencyAudit.json",report);print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--run",type=P.Path,required=True);a=p.parse_args();main(a.root,a.run)
