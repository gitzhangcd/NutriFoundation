"""Execute the actual save handler while editing during the pending request."""
import json
import re
import shutil
import subprocess
from pathlib import Path

def test_pending_save_acknowledges_only_submitted_payload():
    node=shutil.which('node')
    assert node,'Node is required for the asynchronous UI regression'
    source=(Path(__file__).resolve().parents[1]/'web/workbench.js').read_text()
    match=re.search(r"\$\('saveDraft'\)\.onclick=(async\(\)=>\{.*?\});",source,re.S)
    assert match
    handler=match.group(1)
    script='''const assert=require('assert');
let value='A',acknowledge,saving=false;
let draft={payload:{decision_focus:'old'},revision:0,packet_digest:'synthetic'};
const elements={};const $=id=>elements[id]||(elements[id]={textContent:'',disabled:false});
const payload=()=>({decision_focus:value});
let sent;const mutation=(url,body)=>{sent=body;return new Promise(resolve=>acknowledge=resolve)};
const path=()=>'/synthetic/draft';let hook;const afterDraftSaved=(before,after)=>{hook={before,after}};const note=s=>{$('saveStatus').textContent=s};
const handler=HANDLER;
(async()=>{const pending=handler();value='B';acknowledge({revision:1});await pending;
assert.equal(sent.payload.decision_focus,'A');
assert.equal(draft.payload.decision_focus,'A','unsent B must not become acknowledged draft');
assert.equal(value,'B','new edit must be preserved');
assert.equal($('freeze').disabled,true,'freeze must stay blocked for unsaved B');
assert.equal(hook.before.decision_focus,'old');assert.equal(hook.after.decision_focus,'A','links are re-evaluated against the acknowledged payload');})().catch(e=>{console.error(e);process.exit(1);});
'''.replace('HANDLER',handler)
    result=subprocess.run([node,'-e',script],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
