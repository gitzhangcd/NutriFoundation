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


def test_saved_edit_invalidates_previous_link_before_refetch():
    module=Path(__file__).resolve().parents[1]/'web/evidence_status.js'
    script="""
import {invalidateChangedBindings} from MODULE;
import assert from 'node:assert/strict';
const itemText=(data,field,index)=>Array.isArray(data[field])?data[field][index]:index===0?data[field]:undefined;
const bindings=[{field:'facts',item_index:0,current_statement_matches:true},{field:'facts',item_index:1,current_statement_matches:true},
                {field:'focus',item_index:0,current_statement_matches:true}];
const before={facts:['A','B'],focus:'Q'};
let out=invalidateChangedBindings(bindings,before,{facts:['A edited','B'],focus:'Q'},itemText);
assert.deepEqual(out.map(b=>b.current_statement_matches),[false,true,true]);
out=invalidateChangedBindings(bindings,before,{facts:['B'],focus:'Q'},itemText);
assert.deepEqual(out.map(b=>b.current_statement_matches),[false,false,true],'removal shifts indexes: both links need review');
out=invalidateChangedBindings(bindings,before,before,itemText);
assert.equal(out[0],bindings[0],'unchanged statements keep the server record');
""".replace('MODULE',repr('data:text/javascript;base64,'+base64.b64encode(module.read_bytes()).decode()))
    r=subprocess.run(['node','--input-type=module','-e',script],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
