import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project import catalog, path, read_json, write_json
import zipfile
_, release, _ = catalog()
recipe = read_json(path(release["recipe"]) / "recipe.json")
path(".build/checks").mkdir(parents=True, exist_ok=True)
from pathlib import Path
import struct,json
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
b=zipfile.ZipFile(path(release["file"])).read(recipe["native"]["path"])
native=recipe["native"]
shim=native["shimAddress"];hookaddr=native["hookAddress"];register=native["originalCallTarget"];bridge=native["javaBridgeAddress"]
results=[]
for slide in [0,0x10000000,0x30000000,0x60000000]:
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(slide,0x1000000);u.mem_write(slide,b)
 stack=0x70000000;u.mem_map(stack,0x10000);sp=stack+0x8000
 u.reg_write(UC_ARM_REG_SP,sp)
 for reg,value in [(UC_ARM_REG_R0,0x1111),(UC_ARM_REG_R1,0x2222),(UC_ARM_REG_R2,0x3333),(UC_ARM_REG_R3,0x4444),(UC_ARM_REG_R4,0x5555),(UC_ARM_REG_R5,0x6666),(UC_ARM_REG_R6,0x7777),(UC_ARM_REG_R7,0x8888),(UC_ARM_REG_R8,0x9999),(UC_ARM_REG_R9,0xaaaa),(UC_ARM_REG_R10,0xbbbb),(UC_ARM_REG_R11,0xcccc)]:u.reg_write(reg,value)
 u.mem_write(sp,struct.pack("<2I",0x12345678,0));calls=[];launched=[]
 def cstr(ptr):
  if ptr==0:return None
  return bytes(u.mem_read(ptr,100)).split(b"\0")[0].decode()
 def code_hook(uc,address,size,data):
  if address==slide+hookaddr+4:
   uc.emu_stop();return
  if address==slide+register:
   args=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]+list(struct.unpack("<2I",uc.mem_read(uc.reg_read(UC_ARM_REG_SP),8)))
   assert uc.reg_read(UC_ARM_REG_SP)%8==0
   calls.append(args)
   if len(calls)==1:
    assert args==[0x1111,0x2222,0x3333,0x4444,0x12345678,0]
   else:
    assert cstr(args[0])=="button_dts_pcm_settings"
    assert cstr(args[1])=="dts_pcm_setting_label"
    assert cstr(args[2])=="dts_pcm_setting_button"
    assert args[3]==0 and args[5]==0
    assert args[4]==slide+shim+native["callbackOffset"]
   uc.reg_write(UC_ARM_REG_R0,0xdeadbeef if len(calls)==1 else 0x1234)
   for reg in [UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12]:uc.reg_write(reg,0xfefefefe)
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  if address==slide+bridge:
   args=[uc.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]+list(struct.unpack("<2I",uc.mem_read(uc.reg_read(UC_ARM_REG_SP),8)))
   assert cstr(args[0])=="com.dunehd.pcm.DTS_SETTINGS" and args[1:]==[0,0,0,0,0]
   launched.append(True);uc.reg_write(UC_ARM_REG_R0,1);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,code_hook)
 u.emu_start(slide+hookaddr,slide+0xffffff,count=200)
 assert len(calls)==2 and u.reg_read(UC_ARM_REG_R0)==0xdeadbeef and u.reg_read(UC_ARM_REG_SP)==sp
 for reg,value in [(UC_ARM_REG_R4,0x5555),(UC_ARM_REG_R5,0x6666),(UC_ARM_REG_R6,0x7777),(UC_ARM_REG_R7,0x8888),(UC_ARM_REG_R8,0x9999),(UC_ARM_REG_R9,0xaaaa),(UC_ARM_REG_R10,0xbbbb),(UC_ARM_REG_R11,0xcccc)]:assert u.reg_read(reg)==value
 u.reg_write(UC_ARM_REG_LR,slide+hookaddr+4)
 u.emu_start(calls[1][4],slide+0xffffff,count=100)
 assert launched==[True] and u.reg_read(UC_ARM_REG_SP)==sp and u.reg_read(UC_ARM_REG_R4)==0x5555
 results.append({"loadAddress":hex(slide),"originalRegistrationPreserved":True,"newButtonRegistered":True,"stackAndCalleeSavedRegistersPreserved":True,"dialogActionArgumentsCorrect":True})
write_json(path(".build/checks/native.json"), results);print("PASS: ARM registration shim and callback at four ASLR load addresses")
