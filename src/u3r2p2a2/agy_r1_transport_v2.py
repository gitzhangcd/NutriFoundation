"""R1-v0.2: semantic row projection, preserving full immutable carrier table.
All reviewer choices and original full-schema reconstruction remain v0.1."""
from agy_r1_transport import COMMON,TRANSPORT,table
from agy_raw_standard_browser import canon
def review_prompt(src,q,hits,rules):
 rows,groups=table(hits,q)
 # Carrier SHA/locator are fixed local evidence bindings, not semantic
 # information. Every returned row/label/alias/definition is retained.
 tab=[[i+1,r["target_key"][0],r["target_key"][1],r["target_key"][2],r["target_native_label"],r.get("raw_aliases",[]),r.get("raw_definition","")] for i,r in enumerate(rows)]
 return COMMON+"Task rules:\n"+canon(rules)+"\n"+TRANSPORT+"\nReturn concise substantive judgments; do not repeat the table. All locator and SHA strings are fixed in the local full evidence table and will be copied using the row indices you select. No semantic field is supplied by the controller.\nSource evidence 0:\n"+canon(src)+"\nActual queries and result row indices:\n"+canon(groups)+"\nRaw semantic rows, columns [row,system,version,native_id,label,raw_aliases,raw_definition]:\n"+canon(tab)
