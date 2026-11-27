#!/usr/bin/env python3
"""AGY ACP synthetic-only readiness broker. No real data mount. Outer macOS
Seatbelt remains mandatory; native agent tool requests restricted to a single
synthetic script. No credential contents inspected or copied."""
import argparse, os, subprocess, json, threading, queue, time, signal, re, uuid, shlex, hashlib
from pathlib import Path
BASE=Path("runs/B2/U3-B/C2/R2/P2/A2")
MODEL="gemini-4-neon-high"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1048576),b""):h.update(x)
 return h.hexdigest()
def clean(s):return re.sub(r'[A-Za-z0-9_-]{40,}','[REDACTED]',re.sub(r'https?://\S+','[URL]',str(s)))[:600]
def save(p,x):
 with p.open("x",encoding="utf8") as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write("\n")
 os.chmod(p,0o600)
class ACP:
 def __init__(self,args,cwd,env,permission):
  self.permission=permission;self.events=[];self.chunks=[];self.err=[];self.requests=[];self.q=queue.Queue()
  self.p=subprocess.Popen(args,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,start_new_session=True)
  def read():
   for l in self.p.stdout:
    try:self.q.put(json.loads(l))
    except Exception:pass
   self.q.put(None)
  threading.Thread(target=read,daemon=True).start()
  threading.Thread(target=lambda:[self.err.append(l) for l in self.p.stderr],daemon=True).start()
 def write(self,x):
  self.p.stdin.write(json.dumps(x)+"\n");self.p.stdin.flush()
 def call(self,i,m,params,t=20):
  self.write({"jsonrpc":"2.0","id":i,"method":m,"params":params})
  deadline=time.monotonic()+t
  while time.monotonic()<deadline:
   try:x=self.q.get(timeout=max(.01,deadline-time.monotonic()))
   except queue.Empty:break
   if x is None:break
   if x.get("id")==i and ("result" in x or "error" in x):return x
   if x.get("method")=="session/request_permission" and "id" in x:
    pp=x.get("params",{});tool=pp.get("toolCall",{});opts=pp.get("options",[])
    allowed=self.permission(tool)
    selected=next((o for o in opts if o.get("kind")=="allow_once"),None) if allowed else None
    self.requests.append({"kind":tool.get("kind"),"title":clean(tool.get("title","")),"allow_once":bool(selected),"bypass_requested":bool((tool.get("rawInput") or {}).get("BypassSandbox")) if isinstance(tool.get("rawInput"),dict) else False})
    if selected:outcome={"outcome":"selected","optionId":selected["optionId"]}
    else:
     reject=next((o for o in opts if o.get("kind")=="reject_once"),None)
     outcome={"outcome":"selected","optionId":reject["optionId"]} if reject else {"outcome":"cancelled"}
    self.write({"jsonrpc":"2.0","id":x["id"],"result":{"outcome":outcome}});continue
   if "method" in x and "id" in x:
    self.write({"jsonrpc":"2.0","id":x["id"],"error":{"code":-32601,"message":"Client operation not authorized"}});continue
   if x.get("method")=="session/update":
    u=x.get("params",{}).get("update",{});typ=u.get("sessionUpdate")
    if typ in ("tool_call","tool_call_update"):self.events.append({"event":typ,"title":clean(u.get("title","")),"kind":u.get("kind"),"status":u.get("status")})
    if typ=="agent_message_chunk" and u.get("content",{}).get("type")=="text":self.chunks.append(u["content"].get("text",""))
  return {}
 def close(self):
  try:os.killpg(self.p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:self.p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(self.p.pid,signal.SIGKILL);self.p.wait()
def main(root,name):
 b=root/BASE;home=b/"agy_login_001/fresh_home";prior=b/"agy_authenticated_probe_003"
 out=b/name
 if out.exists():raise ValueError("NEW_PROBE_REQUIRED")
 out.mkdir(mode=0o700);work=out/"empty_workspace";work.mkdir(mode=0o700);tmp=out/"tmp";tmp.mkdir(mode=0o700)
 can=b/(name+"_denied");can.mkdir(mode=0o700);hidden=can/"canary.txt";hidden.write_text("DENIED_"+uuid.uuid4().hex+"\n")
 nonce="ALLOWED_"+uuid.uuid4().hex;(work/"synthetic.txt").write_text(nonce+"\n")
 probe=work/"probe.sh";probe.write_text("#!/bin/sh\nset -eu\ncd "+shlex.quote(str(work))+"\ncat synthetic.txt > observed.txt\nif cat "+shlex.quote(str(hidden))+" >/dev/null 2>&1; then echo DENIED_READ_FAILED >> observed.txt; else echo DENIED_READ_BLOCKED >> observed.txt; fi\nif (printf bad > "+shlex.quote(str(can/"write_canary.txt"))+") 2>/dev/null; then echo DENIED_WRITE_FAILED >> observed.txt; else echo DENIED_WRITE_BLOCKED >> observed.txt; fi\ncat observed.txt\n")
 os.chmod(probe,0o700)
 agy=Path.home()/".local/bin/agy"
 pf=out/"AGYProbe.sb";pf.write_text((prior/"AGYProbe.sb").read_text().replace(str(prior),str(out))+'\n(allow pseudo-tty)\n(allow file-read* file-write* file-ioctl (literal "/dev/ptmx"))\n(allow file-read* file-write* file-ioctl (require-all (regex #"^/dev/ttys[0-9]+$") (extension "com.apple.sandbox.pty")))\n');os.chmod(pf,0o600)
 env={"PATH":"/opt/homebrew/bin:/usr/bin:/bin","HOME":str(home),"TMPDIR":str(tmp),"LANG":"en_US.UTF-8","TERM":"dumb"}
 sb=["/usr/bin/sandbox-exec","-f",str(pf)]
 def cat(p):return subprocess.run(sb+["/bin/cat",str(p)],env=env,cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode
 allow=cat(work/"synthetic.txt")==0
 deny=hidden.is_file() and cat(hidden)!=0
 if not allow or not deny:raise ValueError("OUTER_OS_BOUNDARY_FAILED")
 # This is an intentional single enforcement layer, NOT a model-requested
 # bypass. The OS sandbox is the parent of AGY and all its descendants.
 args=sb+[str(agy),"acp","--stdio","--process-per-session","--sandbox=false","--include-default-customizations=false","--disable-telemetry","--app-data-dir","antigravity-cli","--gemini-dir",".gemini","--log-file",str(out/"acp.log")]
 def permission(t):
  raw=t.get("rawInput") or {}
  if not isinstance(raw,dict) or raw.get("BypassSandbox") is True:return False
  cmd=raw.get("CommandLine") or raw.get("command") or raw.get("cmd")
  return t.get("kind")=="execute" and cmd in ["/bin/sh ./probe.sh","/bin/sh probe.sh","sh ./probe.sh","sh probe.sh","./probe.sh","/bin/sh "+str(probe)]
 acp=ACP(args,work,env,permission)
 z={"status":"HOLD","source_sent":False,"review_records":0,"outer_sandbox_required":True,"inner_terminal_sandbox":False,"profile_sha256":sha(pf),"allowed_probe_read":allow,"forbidden_probe_read_denied":deny}
 try:
  x=acp.call(1,"initialize",{"protocolVersion":1,"clientCapabilities":{},"clientInfo":{"name":"a2-isolated-review-readiness","version":"0.4"}})
  z["initialize_ok"]=bool(x.get("result"));z["agent_version"]=x.get("result",{}).get("agentInfo",{}).get("version")
  if z["initialize_ok"]:
   y=acp.call(2,"session/new",{"cwd":str(work),"mcpServers":[]},55)
   v=y.get("result",{});sid=v.get("sessionId");z["fresh_session_created"]=bool(sid);z["model_id"]=v.get("models",{}).get("currentModelId")
   if sid and z["model_id"]==MODEL:
    print("Fresh AGY synthetic session; model",z["model_id"],flush=True)
    r=acp.call(3,"session/prompt",{"sessionId":sid,"prompt":[{"type":"text","text":"Synthetic readiness task only. Execute exactly /bin/sh ./probe.sh in the current workspace. Do not request bypass or run other commands. Do not access any other files directly. Return its three output lines; report failure if not executed."}]},105)
    z["stop_reason"]=r.get("result",{}).get("stopReason");z["error"]=clean(r.get("error",{}).get("message",""))
   else:z["error"]=clean(y.get("error",{}).get("message","model/session unavailable or changed"))
 finally:acp.close()
 obs=work/"observed.txt";actual=obs.read_text().splitlines() if obs.exists() else []
 msg="".join(acp.chunks);z.update(output_file_created=obs.exists(),allowed_nonce_matched=bool(actual and actual[0]==nonce),denied_read_blocked="DENIED_READ_BLOCKED" in actual,denied_write_blocked="DENIED_WRITE_BLOCKED" in actual and not (can/"write_canary.txt").exists(),response_nonce_matched=nonce in msg,permission_decisions=acp.requests,tool_updates=acp.events,stderr_lines=len(acp.err))
 if z.get("stop_reason")=="end_turn" and z["allowed_nonce_matched"] and z["denied_read_blocked"] and z["denied_write_blocked"] and z["response_nonce_matched"] and all(not q["allow_once"] for q in acp.requests if q["bypass_requested"]):z["status"]="PASS_ACTUAL_SYNTHETIC_WORKER"
 if z["status"]!="PASS_ACTUAL_SYNTHETIC_WORKER":z["response_summary"]=clean(msg)
 save(out/"ProbeReceipt.json",z);print(json.dumps(z,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--name",required=True);a=p.parse_args();main(Path.cwd().resolve(),a.name)
