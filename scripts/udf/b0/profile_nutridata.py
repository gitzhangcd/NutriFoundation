#!/usr/bin/env python3
"""B0/U1-A source-only OOXML metadata audit. No workbook edits or remote requests.
Exact scan of materialized nonempty rows; raw tokens and JSON cells stay local.
A key match is statistical evidence, not a qualified semantic mapping.
"""
import argparse
import collections as C
import datetime as DT
import hashlib
import json
import math
import pathlib as P
import posixpath
import re
import zipfile
import xml.etree.ElementTree as E
from decimal import Decimal, InvalidOperation

M = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
MISSING = {'tr','trace','—','–','-','na','n/a','null','none','nan','未测','未检出','不详','未知','<lod','nd','n.d.','无','缺失','微量','t','*'}
MACROS = {'calorie','protein','fat','carbohydrate','na','edible','water_rate','dietary_fiber','vitamin_a','folic_acid','gi','gl'}
# Store raw numeric-looking string values for parsing, never normalize identifiers to int.
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def num(v):
 try:
  if v is None or isinstance(v,bool):return None
  q=Decimal(str(v).strip())
  return q if q.is_finite() else None
 except (InvalidOperation,ValueError):return None
def key(v):
 return None if v is None or str(v).strip()=='' else str(v)
def cell(c,ss):
 t=c.get('t','n')
 v=c.find(M+'v')
 v=v.text if v is not None else None
 if t=='s' and v is not None:v=ss[int(v)]
 if t=='inlineStr':v=''.join(x.text or '' for x in c.iter(M+'t'))
 return v,t,c.find(M+'f') is not None
def read_rows(z,path,ss):
 with z.open(path) as f:
  for _,e in E.iterparse(f,events=('end',)):
   if e.tag==M+'row':
    row={}
    for c in e.findall(M+'c'):
     col=re.sub(r'\d+','',c.get('r',''))
     if not col:raise ValueError('cell missing explicit coordinate')
     if col in row:raise ValueError('duplicate cell coordinate')
     row[col]=cell(c,ss)
    yield int(e.get('r','0')),row
    e.clear()
def sheets(z):
 rel={e.get('Id'):e.get('Target') for e in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
 for s in E.fromstring(z.read('xl/workbook.xml')).find(M+'sheets'):
  t=rel[s.get(R+'id')]
  path=t.lstrip('/') if t.startswith('/') else posixpath.normpath(posixpath.join('xl',t))
  yield s.get('name'),s.get('state','visible'),path
def json_obj(v):
 if v is None or not str(v).strip():return 'blank',None
 try:
  # Reject duplicate JSON object keys and non-standard NaN/Infinity, rather than silently overwriting.
  def no_dupes(pairs):
   d={}
   for k,x in pairs:
    if k in d:raise ValueError('duplicate JSON key')
    d[k]=x
   return d
  def bad_const(v):raise ValueError('nonstandard numeric constant')
  x=json.loads(v,object_pairs_hook=no_dupes,parse_constant=bad_const)
  return ('object' if isinstance(x,dict) else 'non_object'),x
 except (ValueError,TypeError,RecursionError):return 'invalid',None
def write_json(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def key_stats(xs):
 c=C.Counter(v for v in xs if v is not None)
 return {'rows':len(xs),'missing':sum(v is None for v in xs),'distinct_nonblank':len(c),'duplicate_rows':sum(n for n in c.values() if n>1),'duplicate_excess':sum(n-1 for n in c.values() if n>1),'unique_nonblank':all(n==1 for n in c.values()) and None not in xs and bool(xs)}
def cmp_num(a,b):
 x,y=num(a),num(b)
 return None if x is None or y is None else x==y
def token(v):
 if v is None:return 'blank'
 s=str(v).strip()
 if not s:return 'whitespace'
 if s.lower() in MISSING:return 'token:'+s
 n=num(s)
 if n is not None:
  return 'numeric_zero' if n==0 else 'numeric_nonzero'
 if re.match(r'^[<≤>≥]',s):return 'inequality'
 return 'other'
def jkeys(obj,counts):
 for k,v in obj.items():counts[k+'::'+type(v).__name__]+=1
def values_map(obj):
 groups=obj.get('nutritionMap')
 if not isinstance(groups,dict):return []
 return [v for a in groups.values() if isinstance(a,list) for v in a if isinstance(v,dict)]
def unit_summary(objs):
 return dict(C.Counter(str(v.get('unit','MISSING')) for v in objs))
def check_asserts():
 assert token(None)=='blank' and token('0')=='numeric_zero' and token('Tr')=='token:Tr'
 assert key('001')!='1'
 assert json_obj('{"id":1,"id":2}')[0]=='invalid'
 assert json_obj('{"x":NaN}')[0]=='invalid'
 assert key_stats(['a','a',None])['duplicate_excess']==1
 assert cmp_num('1.0','1') is True and cmp_num('Tr','0') is None
 assert cell(E.fromstring('<c xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" r="A1" t="inlineStr"><is><t>001</t></is></c>'),[])[0]=='001'
 assert cell(E.fromstring('<c xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" r="A1"><f>1+1</f><v>2</v></c>'),[])[2] is True
def profile(root,out):
 root=root.resolve(strict=True)
 out=out.resolve()
 if root==out or root in out.parents or out.exists():raise ValueError('output must be new and outside source directory')
 out.mkdir(parents=True)
 private=out/'private';private.mkdir()
 manifest=[];profiles=[];errors=[];samples=[];ingredient=[];dish=[];core={}
 for p in sorted(root.iterdir()):
  if p.is_symlink():
   errors.append({'file':p.name,'error':'symlink excluded'});continue
  if not p.is_file() or p.suffix.lower()!='.xlsx':continue
  before=sha(p); entry={'file':p.name,'size_bytes':p.stat().st_size,'sha256':before,'asset_id':'NDF-G023-'+p.name.split('-')[0],'mtime_utc':DT.datetime.fromtimestamp(p.stat().st_mtime,DT.timezone.utc).isoformat()}
  manifest.append(entry)
  try:
   with zipfile.ZipFile(p) as z:
    # Whole archive CRC check, not just first rows. Sheet XML consumed fully.
    bad=z.testzip()
    if bad:raise ValueError('CRC failure: '+bad)
    entry['zip_crc']='PASS'
    entry['zip_entries']=len(z.infolist())
    ss=[''.join(t.text or '' for t in si.iter(M+'t')) for si in E.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
    for sheet,state,path in sheets(z):
     hdr=None; header_row=None; columns={}; coltypes={}; names={}; ks={k:[] for k in ('id','item_id','name','chinese_name','code','id+item_id')}; jstatus={k:C.Counter() for k in ('list_json','detail_json')}; jshape={k:C.Counter() for k in jstatus}; jc=C.Counter(); cstats=C.Counter(); nutrient_units=C.Counter(); nutrient_tokens=C.Counter(); nutrient_attr=C.Counter(); history_sources=set(); rows=0; blankrows=0; extra=0; last=0; duplicates=0; first_seen=set()
     is_ingredient=p.name.startswith('01-')
     is_dish=p.name.startswith('02-')
     for rn,row in read_rows(z,path,ss):
      last=max(last,rn)
      if not any(v[0] not in (None,'') for v in row.values()):
       blankrows+=1;continue
      if hdr is None:
       hdr={c:v[0] for c,v in row.items() if v[0] not in (None,'')}
       header_row=rn
       duplicates=len(hdr)-len(set(hdr.values()))
       for c,n in hdr.items():
        columns[c]=C.Counter();coltypes[c]=C.Counter();names[c]=n
       continue
      rows+=1
      extra+=sum(c not in hdr and v[0] not in (None,'') for c,v in row.items())
      data={n:row.get(c,(None,'absent',False))[0] for c,n in hdr.items()}
      for c,n in hdr.items():
       v,t,formula=row.get(c,(None,'absent',False))
       columns[c][token(v)]+=1
       if formula:columns[c]['formula_cells']+=1
       coltypes[c][t]+=1
      for k in ks:
       if k=='id+item_id':
        a,b=key(data.get('id')),key(data.get('item_id'));ks[k].append((a,b) if a is not None and b is not None else None)
       else:ks[k].append(key(data.get(k)))
      # For privacy retain at most three core source records, local only.
      if (is_ingredient or is_dish) and rows<=3:samples.append({'file':p.name,'sheet':sheet,'excel_row':rn,'values':data})
      objs={}
      for k in jstatus:
       st,obj=json_obj(data.get(k));jstatus[k][st]+=1
       if st=='object':
        objs[k]=obj;jkeys(obj,jshape[k])
        a=key(obj.get('id'))
        for target in ('id','item_id'):
         b=key(data.get(target))
         jc[k+':'+target+':'+('missing' if a is None or b is None else ('equal' if a==b else 'different'))]+=1
        a,b=key(obj.get('name')),key(data.get('name'))
        jc[k+':name:'+('missing' if a is None or b is None else ('equal' if a==b else 'different'))]+=1
      d=objs.get('detail_json')
      if not d:continue
      if is_ingredient or is_dish:
       nv=values_map(d);cstats['rows_with_nutritionMap']+=bool(nv);cstats['nutrition_entries']+=len(nv)
       for v in nv:
        ident=str(v.get('desc',v.get('name','MISSING')))
        nutrient_units[ident+' | '+str(v.get('unit','MISSING'))]+=1
        nutrient_tokens[ident+' | '+token(v.get('value'))]+=1
        nutrient_attr[ident]+=1
       cstats['rows_with_portion_list']+=isinstance(d.get('ingredientUnit' if is_ingredient else 'unit'),list) and bool(d.get('ingredientUnit' if is_ingredient else 'unit'))
       # Candidate numeric equivalence of native wide vs nested macro values only.
       by_desc={str(v.get('desc','')).lower():v.get('value') for v in nv}
       for col in ('calorie','protein','fat','carbohydrate','na'):
        alias={'carbohydrate':'carbohydrate','na':'na'}.get(col,col)
        if col in data and alias in by_desc:
         equal=cmp_num(data[col],by_desc[alias]);cstats['wide_nested:'+col+':'+('not_numeric' if equal is None else 'equal' if equal else 'different')]+=1
      if is_ingredient:
       source=key(d.get('source'));cstats['rows_with_source']+=source is not None
       if source:history_sources.add(source)
       h=d.get('nutrientHistoryMap');cstats['rows_with_nonempty_history']+=bool(h) and isinstance(h,dict)
       ingredient.append({'id':key(data.get('id')),'item_id':key(data.get('item_id')),'detail_id':key(d.get('id')),'code':key(d.get('code')),'name':key(d.get('name')),'row':rn})
      if is_dish:
       major=d.get('major');steps=d.get('dishCooksteps')
       cstats['rows_with_steps']+=isinstance(steps,list) and bool(steps)
       cstats['rows_with_nonempty_major']+=isinstance(major,list) and bool(major)
       if not isinstance(major,list):cstats['major_not_list']+=1;continue
       if not major:cstats['major_empty']+=1
       for idx,m in enumerate(major):
        cstats['major_entries']+=1
        if not isinstance(m,dict):cstats['major_non_object']+=1;continue
        n=num(m.get('note')); cstats['note_numeric' if n is not None else 'note_not_numeric']+=1
        if n is not None and n<=0:cstats['note_nonpositive']+=1
        dish.append({'dish_row':rn,'dish_item_id':key(data.get('item_id')),'major_index':idx,'ingrId':key(m.get('ingrId')),'code':key(m.get('code')),'name':key(m.get('name'))})
     if hdr is None:hdr={}
     present_keys={k:key_stats(v) for k,v in ks.items() if any(x is not None for x in v)}
     summary={'file':p.name,'asset_id':entry['asset_id'],'sheet':sheet,'sheet_state':state,'header_row':header_row,'columns':len(hdr),'rows':rows,'last_row':last,'explicit_empty_rows':blankrows,'duplicate_header_count':duplicates,'outside_header_nonempty_cells':extra,'fields':[{'column':c,'name':n,'tokens':dict(columns[c]),'ooxml_types':dict(coltypes[c])} for c,n in hdr.items()],'keys':present_keys,'json_status':{k:dict(v) for k,v in jstatus.items()},'json_top_keys':{k:dict(v) for k,v in jshape.items()},'json_consistency':dict(jc)}
     profiles.append(summary)
     if is_ingredient or is_dish:core['ingredient' if is_ingredient else 'dish']={'counts':dict(cstats),'nutrient_units':dict(nutrient_units),'nutrient_tokens':dict(nutrient_tokens),'nutrient_attr':dict(nutrient_attr),'distinct_source_strings':len(history_sources)}
   entry['sha256_after']=sha(p);entry['unchanged']=entry['sha256_after']==before
   if not entry['unchanged']:errors.append({'file':p.name,'error':'source changed during scan'})
  except Exception as ex:
   errors.append({'file':p.name,'error':type(ex).__name__+': '+str(ex)[:160]})
 # Independent comparisons of every candidate foreign key against separately indexed parent IDs.
 joins={}
 for field in ('id','item_id','detail_id','code'):
  index=C.defaultdict(list)
  for i in ingredient:
   if i[field] is not None:index[i[field]].append(i)
  child_field='code' if field=='code' else 'ingrId'
  c=C.Counter();dish_rows=C.defaultdict(lambda:[0,0])
  for m in dish:
   x=m[child_field];matched=index.get(x,[]) if x is not None else []
   c['child_rows']+=1;dish_rows[m['dish_row']][0]+=1
   c['missing_child_key']+=x is None
   c['zero_matches']+=not matched
   c['one_match']+=len(matched)==1
   c['multiple_matches']+=len(matched)>1
   c['inner_join_rows']+=len(matched)
   c['left_join_rows']+=max(1,len(matched))
   if len(matched)==1:
    dish_rows[m['dish_row']][1]+=1
    for attr in ('code','name'):
     a,b=m[attr],matched[0][attr]
     c[attr+'_compare_missing' if a is None or b is None else attr+'_exact_equal' if a==b else attr+'_different']+=1
  c['dishes_with_all_lines_one_match']=sum(a==b for a,b in dish_rows.values())
  c['dishes_with_lines']=len(dish_rows)
  c['parent_distinct_nonblank_keys']=len(index)
  c['parent_duplicate_keys']=sum(len(v)>1 for v in index.values())
  joins['major.'+child_field+' -> ingredient.'+field]=dict(c)
 # Cross-sub库 ID reuse (not an automatic join).
 id_counts=C.Counter()
 # Detailed fields and hashes contain no individual raw cells; local only.
 write_json(private/'NativeFileManifest.json',manifest)
 write_json(private/'NativeTableProfiles.json',profiles)
 write_json(private/'CoreRawSamples.json',samples)
 write_json(private/'CoreLinkAudit.json',{'core':core,'joins':joins})
 # Shareable summaries only; no row-level IDs, names, media URLs, source text or local absolute paths.
 compact=[]
 for a in profiles:
  cols={f['name']:f['tokens'] for f in a['fields'] if f['name'] in MACROS}
  compact.append({'asset_id':a['asset_id'],'file':a['file'],'sheet':a['sheet'],'rows':a['rows'],'columns':a['columns'],'header_row':a['header_row'],'last_row':a['last_row'],'duplicate_header_count':a['duplicate_header_count'],'outside_header_nonempty_cells':a['outside_header_nonempty_cells'],'key_id':a['keys'].get('id'),'key_item_id':a['keys'].get('item_id'),'json_status':a['json_status'],'macro_tokens':cols if a['file'].startswith(('01-','02-','07-')) else {}})
 report={'schema':'B0-NUTRIDATA-PROFILE-0.1','method':'full nonempty OOXML row scan, first nonempty row header; no formula recalculation; exact text keys; no unit inference','run_time_utc':DT.datetime.now(DT.timezone.utc).isoformat(),'script_sha256':sha(P.Path(__file__)),'workbooks_found':len(manifest),'workbooks_crc_pass':sum(m.get('zip_crc')=='PASS' for m in manifest),'workbooks_unchanged':sum(m.get('unchanged',False) for m in manifest),'total_file_bytes':sum(m['size_bytes'] for m in manifest),'sheets_profiled':len(profiles),'nonempty_data_rows':sum(a['rows'] for a in profiles),'errors':errors,'tables':compact,'core':{k:{'counts':v['counts'],'distinct_source_strings':v['distinct_source_strings'],'nutrient_units':v['nutrient_units'],'nutrient_attr':v['nutrient_attr']} for k,v in core.items()},'joins':joins}
 write_json(out/'summary_shareable.json',report)
 print(json.dumps({'workbooks_found':report['workbooks_found'],'crc_pass':report['workbooks_crc_pass'],'unchanged':report['workbooks_unchanged'],'sheets':report['sheets_profiled'],'rows':report['nonempty_data_rows'],'bytes':report['total_file_bytes'],'errors':errors,'tables':[{k:a[k] for k in ('asset_id','file','rows','columns','key_id','key_item_id','json_status')} for a in compact],'core':{k:v['counts'] for k,v in core.items()},'joins':joins},ensure_ascii=False,separators=(',',':')))
 return report
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=P.Path);ap.add_argument('--out',type=P.Path);ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
 check_asserts()
 if a.self_test:print('8 smoke assertions passed')
 else:
  if not a.root or not a.out:ap.error('--root and --out required')
  profile(a.root,a.out)
