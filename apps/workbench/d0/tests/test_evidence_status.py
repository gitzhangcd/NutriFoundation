"""Evidence status must not overclaim PDF verification or stale linkage."""
import subprocess
import base64
from pathlib import Path

def test_independent_evidence_status():
    module=Path(__file__).resolve().parents[1]/'web/evidence_status.js'
    script="""
import {judgmentEvidence} from MODULE;
import assert from 'node:assert/strict';
const b={field:'decision_focus',item_index:0,anchor_id:'a',current_statement_matches:true};
const a={anchor_id:'a',quote:'source',unit_id:'U-1'};
const args={field:'decision_focus',index:0,text:'judgment',savedText:'judgment',bindings:[b],anchors:[a],pdfStatus:{}};
let s=judgmentEvidence(args);assert.equal(s.links.length,1);assert.equal(s.links[0].pdfVerified,false);
s=judgmentEvidence({...args,pdfStatus:{a:true}});assert.equal(s.links[0].pdfVerified,true);
s=judgmentEvidence({...args,text:'edited'});assert.equal(s.links.length,0);assert.equal(s.stale,1);
s=judgmentEvidence({...args,bindings:[]});assert.equal(s.links.length,0);assert.equal(s.stale,0);
s=judgmentEvidence({...args,anchors:[]});assert.equal(s.links.length,0);assert.equal(s.stale,1);
""".replace('MODULE',repr('data:text/javascript;base64,'+base64.b64encode(module.read_bytes()).decode()))
    r=subprocess.run(['node','--input-type=module','-e',script],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
