import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project import catalog, path, read_json, write_json
import zipfile
_, release, _ = catalog()
recipe = read_json(path(release["recipe"]) / "recipe.json")
path(".build/checks").mkdir(parents=True, exist_ok=True)
from loguru import logger
logger.remove()
from androguard.core.dex import DEX
import zipfile,tempfile,json,random
from pathlib import Path
apk=path(release["file"])
d=DEX(zipfile.ZipFile(apk).read("classes.dex"))
clazz=d.get_class("Lcom/dunehd/shell/settings/DtsPcmSettings;")
methods={m.get_name():m for m in clazz.get_methods()}
class VM:
 def __init__(self,root):self.root=Path(root);self.fail_write=False
 def call(self,name,args=()):
  m=methods[name];code=m.get_code();regs=[None]*code.get_registers_size();start=code.get_registers_size()-code.get_ins_size()
  for k,arg in enumerate(args):regs[start+k]=arg
  instr=dict(m.get_instructions_idx());ip=0;result=None;exception=None
  for steps in range(100):
   i=instr[ip];op=i.get_name();a=i.get_operands();nxt=ip+i.get_length()
   try:
    if op.startswith("const-string"):regs[a[0][1]]=a[1][2]
    elif op.startswith("const/"):regs[a[0][1]]=a[1][1]
    elif op=="new-instance":regs[a[0][1]]={"class":a[1][2]}
    elif op.startswith("move-result"):regs[a[0][1]]=result
    elif op=="move-exception":regs[a[0][1]]=exception
    elif op.startswith("invoke-"):
     desc=a[-1][2];values=[regs[x[1]] for x in a[:-1]];method=desc.split("->")[1].split("(")[0]
     if desc.startswith("Lcom/dunehd/shell/settings/DtsPcmSettings;"):result=self.call(method,values)
     elif desc.startswith("Lcom/dunehd/shell/FSFile;"):
      if method=="<init>":
       assert values[1]=="/config/decode_dts_pcm";values[0]["path"]=self.root/"config/decode_dts_pcm";result=None
      elif method=="getFile":result=values[0]["path"]
      else:raise AssertionError(desc)
     elif desc.startswith("Ljava/io/File;"):
      p=values[0]
      if method=="isFile":result=int(p.is_file())
      elif method=="exists":result=int(p.exists())
      elif method=="getParentFile":result=p.parent
      elif method=="mkdirs":
       result=not p.exists()
       if not self.fail_write:p.mkdir(parents=True,exist_ok=True)
      elif method=="createNewFile":
       if self.fail_write:raise PermissionError("injected write failure")
       try:
        with p.open("xb"):pass
        result=1
       except FileExistsError:result=0
      elif method=="delete":
       if self.fail_write:result=0
       else:
        try:p.unlink();result=1
        except FileNotFoundError:result=0
      else:raise AssertionError(desc)
     elif desc.startswith("Landroid/util/Log;"):result=0
     else:raise AssertionError(desc)
    elif op=="if-eqz":
     if not regs[a[0][1]]:nxt=ip+2*a[1][1]
    elif op=="and-int/lit16":regs[a[0][1]]=regs[a[1][1]] & a[2][1]
    elif op.startswith("return"):return regs[a[0][1]]
    else:raise AssertionError(op)
   except (OSError,ValueError) as exc:
    handlers=[off for off,ins in instr.items() if ins.get_name()=="move-exception"]
    if not handlers:raise
    assert code.get_tries_size()>0
    exception=exc;nxt=handlers[0]
   ip=nxt
  raise AssertionError("instruction budget")
with tempfile.TemporaryDirectory(prefix="dune-pcm-policy-") as root:
 v=VM(root);assert v.call("isEnabled")==0
 rng=random.Random(20261105);masks=[0,0xe0,0x41e0,0x40e0,0x4060,0xffff]+[1<<b for b in range(16)]+[rng.randrange(65536) for _ in range(256)]
 for mask in masks:assert v.call("filterMask",[mask])==mask
 assert v.call("save",[1])==1;v=VM(root);assert v.call("isEnabled")==1
 assert v.call("save",[1])==1
 for mask in masks:
  r=v.call("filterMask",[mask]);assert r==mask & ~0x180 and r & 0x4060==mask & 0x4060
 assert v.call("save",[0])==1;v=VM(root);assert v.call("isEnabled")==0
 assert v.call("save",[0])==1
 for mask in masks:assert v.call("filterMask",[mask])==mask
 v.fail_write=True;assert v.call("save",[1])==0;assert v.call("isEnabled")==0
 v.fail_write=False;assert v.call("save",[1])==1
 v.fail_write=True;assert v.call("save",[0])==0;assert v.call("isEnabled")==1
result={"method":"Executed actual DEX instructions in a small interpreter; java.io.File mapped to a temporary host directory, not Android runtime","masksPerState":len(masks),"defaultOff":True,"enabledAndDisabledMasks":True,"DolbyBitsPreserved":True,"persistsAcrossNewInterpreterInstances":True,"idempotentSave":True,"writeFailureAndDeleteFailureReported":True,"AndroidUiRuntimeTested":False}
write_json(path(".build/checks/policy.json"), result);print("PASS: default off, persisted on/off, mask policy, and failed saves using actual DEX instructions")
