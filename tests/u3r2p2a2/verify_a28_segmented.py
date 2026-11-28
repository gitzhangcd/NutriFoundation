"""Synthetic checks for A2.8 execution-only segmented recovery."""
import sys,unittest,copy,ast
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/"src/u3r2p2a2"))
from a28_join_segments import merge_scope_rows,SCOPES,ARMS
def fixture():
 ids={"a","b"};u={s:{(s,"v","x"),(s,"v","y")} for s in SCOPES};caps={(i,s):1 for i in ids for s in SCOPES}
 rows={s:[{"review_id":i,"scope":s,"arm":a,"pool_budget":1,"targets":[[s,"v","x"]]} for i in sorted(ids) for a in ARMS] for s in SCOPES}
 return rows,ids,caps,u
class Test(unittest.TestCase):
 def test_join_closure(self):
  r,i,b,u=fixture();z,c=merge_scope_rows(r,i,b,u);self.assertEqual(len(z),32);self.assertEqual(c,{a:8 for a in ARMS})
 def test_missing_scope(self):
  r,i,b,u=fixture();r.pop(SCOPES[0])
  with self.assertRaises(ValueError):merge_scope_rows(r,i,b,u)
 def test_duplicate_group(self):
  r,i,b,u=fixture();r[SCOPES[0]].append(r[SCOPES[0]][0])
  with self.assertRaises(ValueError):merge_scope_rows(r,i,b,u)
 def test_missing_group(self):
  r,i,b,u=fixture();r[SCOPES[0]].pop()
  with self.assertRaises(ValueError):merge_scope_rows(r,i,b,u)
 def test_wrong_scope(self):
  r,i,b,u=fixture();r[SCOPES[0]][0]["scope"]=SCOPES[1]
  with self.assertRaises(ValueError):merge_scope_rows(r,i,b,u)
 def test_wrong_target(self):
  r,i,b,u=fixture();r[SCOPES[0]][0]["targets"]=[["invalid","v","x"]]
  with self.assertRaises(ValueError):merge_scope_rows(r,i,b,u)
 def test_exceed_cap(self):
  r,i,b,u=fixture();s=SCOPES[0];r[s][0]["targets"].append([s,"v","y"])
  with self.assertRaises(ValueError):merge_scope_rows(r,i,b,u)
 def test_query_no_mutation(self):
  r,i,b,u=fixture();orig=copy.deepcopy(r);merge_scope_rows(r,i,b,u);self.assertEqual(r,orig)
 def test_identical_ranking_algorithm_body(self):
  def blocks(file):
   m=ast.parse((root/"src/u3r2p2a2"/file).read_text());f=next(x for x in m.body if isinstance(x,ast.FunctionDef) and x.name=="main")
   loop=next(x for x in f.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=="s")
   top=next(x for x in m.body if isinstance(x,ast.FunctionDef) and x.name=="top")
   return ast.dump(ast.Module(body=loop.body,type_ignores=[])),ast.dump(top)
  self.assertEqual(blocks("a28_generate.py"),blocks("a28_generate_segment.py"))
if __name__=="__main__":unittest.main()
