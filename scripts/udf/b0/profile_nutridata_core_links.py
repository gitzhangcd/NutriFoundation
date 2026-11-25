#!/usr/bin/env python3
"""B0 focused follow-up, independently re-read the two core workbooks.
Outputs only aggregate checks, with source hashes and no raw food records.
"""
import argparse
import collections as C
import json
import pathlib as P
import zipfile
import xml.etree.ElementTree as E
from profile_nutridata import M,sha,sheets,read_rows,json_obj,key,num,cmp_num,write_json,values_map,token

NUT={'calorie':'能量','protein':'蛋白质','fat':'脂肪','carbohydrate':'碳水化合物','na':'钠','dietary_fiber':'膳食纤维','vitamin_a':'维生素A','folic_acid':'叶酸','carbs_used':'可利用碳水'}
def read_core(p):
 with zipfile.ZipFile(p) as z:
  ss=[''.join(t.text or '' for t in si.iter(M+'t')) for si in E.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
  for _,_,path in sheets(z):
   hdr=None
   for rn,row in read_rows(z,path,ss):
    if not any(v[0] not in (None,'') for v in row.values()):continue
    if hdr is None:
     hdr={c:v[0] for c,v in row.items() if v[0] not in (None,'')};continue
    data={n:row.get(c,(None,'absent',False))[0] for c,n in hdr.items()}
    st,d=json_obj(data.get('detail_json'));lst,l=json_obj(data.get('list_json'))
    yield rn,data,d if st=='object' else {},l if lst=='object' else {}
def compare(data,detail,stats):
 vals=values_map(detail)
 idx=C.defaultdict(list)
 for v in vals:idx[str(v.get('desc',''))].append(v)
 for col,desc in NUT.items():
  if col not in data:continue
  a=idx.get(desc,[])
  if not a:stats[col]['nested_absent']+=1;continue
  if len(a)!=1:stats[col]['nested_multiple']+=1;continue
  w=data.get(col);n=a[0].get('value')
  equal=cmp_num(w,n)
  stats[col]['numeric_equal' if equal is True else 'numeric_different' if equal is False else 'non_numeric_pair']+=1
  if equal is None:stats[col]['non_numeric_raw_exact' if key(w)==key(n) else 'non_numeric_raw_different']+=1
  if equal is False:stats[col]['wide_zero_nested_nonzero' if num(w)==0 and num(n)!=0 else 'other_numeric_difference']+=1
def main(root,out):
 fs=list(root.glob('01-*.xlsx'));ds=list(root.glob('02-*.xlsx'))
 if len(fs)!=1 or len(ds)!=1:raise ValueError('expected exactly one core workbook per prefix')
 f,d=fs[0],ds[0]
 before={p.name:sha(p) for p in (f,d)}
 parents={};codes={};stats={'ingredient':C.defaultdict(C.Counter),'dish':C.defaultdict(C.Counter)}
 counts=C.Counter();unmatched=C.Counter();unmatched_codes=set();qty_types=C.Counter();meta=C.Counter();descriptions=C.Counter();notes=C.Counter()
 for rn,data,j,l in read_core(f):
  counts['ingredient_rows']+=1;compare(data,j,stats['ingredient'])
  item=key(data['item_id'])
  if item in parents:raise ValueError('duplicate parent item_id')
  parents[item]=(key(j.get('code')),key(j.get('name')),rn)
  for n in values_map(j):
   if str(n.get('desc')) in set(NUT.values()):
    descr=str(n.get('description',''))
    # Do not release original descriptions; count explicit denominator hints only.
    normalized=descr.lower().replace(' ','')
    meta['ingredient_core_nutrient_entries']+=1
    if any(t in normalized for t in ('100g','100克','100克可食','每百克','每100g')):meta['ingredient_description_100g_hint']+=1
    if descr.strip():meta['ingredient_nonempty_description']+=1
    if key(n.get('unit')) is None:meta['ingredient_unit_missing']+=1
 for rn,data,j,l in read_core(d):
  counts['dish_rows']+=1;compare(data,j,stats['dish'])
  major=j.get('major',[])
  if not isinstance(major,list):continue
  all_ok=True
  for k,m in enumerate(major):
   if not isinstance(m,dict):counts['malformed_major']+=1;all_ok=False;continue
   counts['lines']+=1
   i=key(m.get('ingrId')); code=key(m.get('code')); name=key(m.get('name'))
   q=num(m.get('note'));qty_types[type(m.get('note')).__name__]+=1
   counts['note_positive']+=q is not None and q>0
   counts['note_unit_field_present']+=any(key(m.get(t)) is not None for t in ('unit','noteUnit','weightUnit','quantityUnit'))
   parent=parents.get(i)
   if parent is None:
    counts['unmatched_lines']+=1;unmatched[i]+=1;unmatched_codes.add(code);all_ok=False;continue
   counts['matched_lines']+=1
   counts['code_exact']+=code==parent[0] and code is not None
   counts['name_exact']+=name==parent[1] and name is not None
   if code!=parent[0] or code is None:all_ok=False
  counts['dishes_all_lines_linked_code_consistent']+=all_ok and bool(major)
  for n in values_map(j):
   if str(n.get('desc')) in set(NUT.values()):
    descr=str(n.get('description',''));norm=descr.lower().replace(' ','')
    meta['dish_core_nutrient_entries']+=1
    meta['dish_description_100g_hint']+=any(t in norm for t in ('100g','100克','100克可食','每百克','每100g'))
    meta['dish_nonempty_description']+=bool(descr.strip())
    meta['dish_unit_missing']+=key(n.get('unit')) is None
 result={'method':'Full two-core-workbook re-read. Numeric equality only, no inferred denominator. Raw identifier strings matched against unique item_id and code cross-check. Name differences are not forced aliases.','counts':dict(counts),'unmatched_distinct_ingrIds':len(unmatched),'unmatched_distinct_codes':len(unmatched_codes),'unmatched_largest_key_frequency':max(unmatched.values(),default=0),'quantity_types':dict(qty_types),'nutrient_metadata_hints':dict(meta),'wide_nested':{k:{c:dict(v) for c,v in x.items()} for k,x in stats.items()},'source_hashes_match':all(sha(p)==before[p.name] for p in (f,d))}
 write_json(out,result)
 print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=P.Path,required=True);a.add_argument('--out',type=P.Path,required=True);x=a.parse_args()
 if x.out.resolve().is_relative_to(x.root.resolve()):raise ValueError('output inside source')
 main(x.root,x.out)
